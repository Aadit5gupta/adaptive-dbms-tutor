"""Bounded FTS5/BM25 retrieval and application-owned source metadata."""

import re
from collections import defaultdict
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import Float, String, column, func, literal_column, or_, select, table, text, tuple_
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.db.models import Passage
from content.schemas.rights import Catalog
from scripts.validate_content import ROOT, load_catalog

TERM = re.compile(r"[^\W_]{2,42}", re.UNICODE)
STOP = frozenset(
    [
        "about",
        "also",
        "and",
        "are",
        "can",
        "could",
        "describe",
        "difference",
        "does",
        "explain",
        "for",
        "from",
        "how",
        "into",
        "is",
        "it",
        "know",
        "me",
        "please",
        "show",
        "should",
        "tell",
        "than",
        "that",
        "the",
        "their",
        "them",
        "these",
        "this",
        "to",
        "use",
        "using",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
        "between",
        "example",
    ]
)
FTS = table("source_passages_fts", column("rowid"))
VOCAB = table("source_passages_fts_vocab", column("doc"))


SourceKind = Literal["book", "lesson"]


class Citation(BaseModel):
    id: str
    kind: SourceKind
    title: str
    url: str
    attribution: str
    license_url: str | None
    lesson_ref: str | None


class PassageHit(BaseModel):
    citation: Citation
    topic_id: str
    text: str
    rank: float
    excerpt: str = ""


def safe_terms(query: str) -> str:
    tokens = list(
        dict.fromkeys(token for token in TERM.findall(query[:500].casefold()) if token not in STOP)
    )
    if "fk" in tokens:
        tokens.extend(("foreign", "key"))
    return " OR ".join(f'"{token}"' for token in tokens[:12])


def approved_books(catalog: Catalog) -> ColumnElement[bool]:
    proofs = [
        (
            book.id,
            clearance.id,
            clearance.approved_content_hash,
            str(clearance.section_url),
            str(clearance.license_url),
            clearance.attribution_text,
        )
        for book in catalog.books
        for clearance in book.section_clearances
        if clearance.indexable
    ]
    return tuple_(
        Passage.book_id,
        Passage.clearance_id,
        Passage.source_hash,
        Passage.source_url,
        Passage.license_url,
        Passage.attribution,
    ).in_(proofs)


def to_citation(passage: Passage) -> Citation:
    return Citation(
        id=passage.passage_key,
        kind="book" if passage.kind == "book" else "lesson",
        title=passage.title,
        url=passage.source_url,
        attribution=passage.attribution,
        license_url=passage.license_url,
        lesson_ref=passage.lesson_ref,
    )


def book_counts(db: Session, catalog: Catalog) -> dict[str, dict[str, int]]:
    searchable_docs = select(VOCAB.c.doc).distinct().subquery()
    result: dict[str, dict[str, int]] = defaultdict(dict)
    rows = db.execute(
        select(Passage.book_id, Passage.clearance_id, func.count())
        .join(searchable_docs, searchable_docs.c.doc == Passage.id)
        .where(Passage.kind == "book", approved_books(catalog))
        .group_by(Passage.book_id, Passage.clearance_id)
    )
    for book_id, clearance_id, count in rows:
        if book_id is not None and clearance_id is not None:
            result[book_id][clearance_id] = count
    return dict(result)


class Retriever:
    def __init__(self, engine: Engine, root: Path = ROOT):
        self.engine = engine
        self.root = root

    def search(
        self,
        query: str,
        topic_ids: tuple[str, ...] = (),
        k: int = 4,
        *,
        kind: SourceKind | None = None,
    ) -> list[PassageHit]:
        terms = safe_terms(query)
        limit = max(0, min(k, 6))
        if not terms or not limit:
            return []

        catalog = load_catalog(self.root)
        rank = literal_column("bm25(source_passages_fts, 2.0, 1.0)", type_=Float()).label("rank")
        excerpt = literal_column(
            "snippet(source_passages_fts, 1, '', '', '…', 36)", type_=String()
        )
        query_ = (
            select(Passage, rank, excerpt)
            .join(FTS, FTS.c.rowid == Passage.id)
            .where(
                text("source_passages_fts MATCH :terms"),
                or_(Passage.kind == "lesson", approved_books(catalog)),
            )
            .order_by(rank, Passage.passage_key)
            .limit(limit)
        )
        if kind is not None:
            query_ = query_.where(Passage.kind == kind)
        with Session(self.engine) as db:
            scoped = (
                list(
                    db.execute(query_.where(Passage.topic_id.in_(topic_ids[:8])), {"terms": terms})
                )
                if topic_ids
                else []
            )
            broader = list(db.execute(query_, {"terms": terms})) if len(scoped) < limit else []
            hits: dict[str, PassageHit] = {}
            for passage, value, preview in [*scoped, *broader]:
                if passage.passage_key not in hits and value < 0:
                    hits[passage.passage_key] = PassageHit(
                        citation=to_citation(passage),
                        topic_id=passage.topic_id,
                        text=passage.body,
                        rank=float(-value),
                        excerpt=preview,
                    )
            return list(hits.values())[:limit]

    def topic_passages(self, topic_id: str, *, k: int = 2) -> list[PassageHit]:
        with Session(self.engine) as db:
            items = db.scalars(
                select(Passage)
                .where(Passage.kind == "lesson", Passage.topic_id == topic_id)
                .order_by(Passage.passage_key)
                .limit(max(0, min(k, 4)))
            )
            return [
                PassageHit(
                    citation=to_citation(passage),
                    topic_id=passage.topic_id,
                    text=passage.body,
                    rank=0,
                )
                for passage in items
            ]
