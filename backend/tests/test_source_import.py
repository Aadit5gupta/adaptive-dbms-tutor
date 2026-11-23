from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.db import open_engine
from app.db.models import Passage
from app.main import ALEMBIC_INI
from app.services.curriculum import publish_content
from app.services.source_import import import_book_section, index_reviewed_lessons
from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from content.schemas.rights import Catalog
from scripts.validate_content import Content, load_content

from .test_rights import TEXT, clearance

BOOK_ID = "bccampus_db_design_2e"
SECTION_URL = "https://opentextbc.ca/dbdesign01/chapter/test/#foreign-keys"


@pytest.fixture
def indexed_db(tmp_path: Path, s1: Path) -> tuple[Engine, Content, Catalog]:
    engine = open_engine(tmp_path / "library.sqlite", create=True)
    cfg = Config(str(ALEMBIC_INI))
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")
    content = load_content(s1)
    with Session(engine) as db, db.begin():
        publish_content(db, content, s1)
    raw = content.catalog.model_dump(mode="json")
    raw["books"][0]["section_clearances"] = [clearance(SECTION_URL)]
    return engine, content, Catalog.model_validate(raw)


def hits(db: Session, query: str) -> list[int]:
    return list(
        db.scalars(
            text("SELECT rowid FROM source_passages_fts WHERE source_passages_fts MATCH :query"),
            {"query": query},
        )
    )


def test_index_reviewed_lessons_idempotently(indexed_db: tuple[Engine, Content, Catalog]) -> None:
    engine, content, _ = indexed_db
    with Session(engine) as db, db.begin():
        assert index_reviewed_lessons(db, content) == 2
        assert index_reviewed_lessons(db, content) == 2
        assert len(hits(db, "synthetic")) == 2
        assert {value for value in db.scalars(select(Passage.kind))} == {"lesson"}


def test_approved_import_is_searchable_and_preserves_real_metadata(
    indexed_db: tuple[Engine, Content, Catalog],
) -> None:
    engine, _, catalog = indexed_db
    with Session(engine) as db, db.begin():
        assert hits(db, "clearance") == []
        assert (
            import_book_section(db, catalog, BOOK_ID, "synthetic_clearance", "sql.joins", TEXT) == 1
        )
        first = hits(db, "clearance")
        assert len(first) == 1
        assert (
            import_book_section(db, catalog, BOOK_ID, "synthetic_clearance", "sql.joins", TEXT) == 1
        )
        assert hits(db, "clearance") == first
        passage = db.get(Passage, first[0])
        assert passage is not None
        assert (
            passage.source_url == SECTION_URL
            and passage.attribution == "Synthetic test attribution"
        )


def test_import_errors_and_rollback_leave_no_searchable_rows(
    indexed_db: tuple[Engine, Content, Catalog],
) -> None:
    engine, content, catalog = indexed_db
    with Session(engine) as db, db.begin():
        with pytest.raises(ValueError, match="hash mismatch"):
            import_book_section(
                db, catalog, BOOK_ID, "synthetic_clearance", "sql.joins", TEXT + b"!"
            )
        with pytest.raises(ValueError, match="no approval"):
            import_book_section(
                db, content.catalog, BOOK_ID, "synthetic_clearance", "sql.joins", TEXT
            )
        assert hits(db, "clearance") == []
    with pytest.raises(RuntimeError), Session(engine) as db, db.begin():
        import_book_section(db, catalog, BOOK_ID, "synthetic_clearance", "sql.joins", TEXT)
        raise RuntimeError("Synthetic failure during import")
    with Session(engine) as db:
        assert hits(db, "clearance") == []
        assert db.scalars(select(Passage)).all() == []


def test_retrieval_applies_current_clearance_and_counts_only_searchable_documents(
    indexed_db: tuple[Engine, Content, Catalog], s1: Path
) -> None:
    from app.services.retrieval import Retriever, book_counts

    from .content_fixtures import save

    engine, content, catalog = indexed_db
    manifest = "content/manifests/books.yaml"
    save(s1, manifest, catalog.model_dump(mode="json"))
    retriever = Retriever(engine, s1)
    with Session(engine) as db, db.begin():
        assert book_counts(db, catalog) == {}
        index_reviewed_lessons(db, content)
        import_book_section(db, catalog, BOOK_ID, "synthetic_clearance", "sql.joins", TEXT)
        assert book_counts(db, catalog) == {BOOK_ID: {"synthetic_clearance": 1}}
    results = retriever.search("explain clearance", ("sql.joins",))
    assert len(results) == 1
    citation = results[0].citation
    assert citation.kind == "book"
    assert citation.url == SECTION_URL
    assert citation.attribution == "Synthetic test attribution"
    assert citation.license_url == "https://creativecommons.org/licenses/by/4.0/"
    assert retriever.search("how does it work") == []
    assert retriever.search('"" (clearance) * AND (junk') == results
    assert retriever.search("synthetic", ("relational.keys",), k=1)[0].citation.kind == "lesson"
    save(s1, manifest, content.catalog.model_dump(mode="json"))
    assert retriever.search("clearance") == []
    with Session(engine) as db:
        assert book_counts(db, content.catalog) == {}


def test_retrieval_bm25_applies_topic_filter_before_broader_fallback(
    indexed_db: tuple[Engine, Content, Catalog], s1: Path
) -> None:
    from app.services.retrieval import Retriever

    engine, content, _ = indexed_db
    with Session(engine) as db, db.begin():
        index_reviewed_lessons(db, content)
    hits_ = Retriever(engine, s1).search("synthetic lesson", ("relational.keys",), k=2)
    assert [hit.topic_id for hit in hits_] == ["relational.keys", "sql.joins"]
    assert all(hit.rank > 0 for hit in hits_)


def test_curated_tutor_and_mock_provider_cannot_invent_citations(
    indexed_db: tuple[Engine, Content, Catalog], s1: Path
) -> None:
    import asyncio

    from app.providers.contracts import ProviderAnswer, ProviderUnavailable, TutorContext
    from app.schemas.tutor import TutorInput
    from app.services.retrieval import Retriever
    from app.services.tutor import TutorService

    engine, content, _ = indexed_db
    retriever = Retriever(engine, s1)
    request = TutorInput(query="Explain the concept", topic_id="relational.keys")
    with Session(engine) as db, db.begin():
        index_reviewed_lessons(db, content)

    class MockProvider:
        async def respond(self, context: TutorContext) -> ProviderAnswer:
            assert context.passages[0].topic_id == "relational.keys"
            return ProviderAnswer("A clear explanation.", (context.passages[0].citation.id,))

    class FabricatedProvider:
        async def respond(self, context: TutorContext) -> ProviderAnswer:
            return ProviderAnswer("A different explanation.", ("made-up-citation",))

    class UnavailableProvider:
        async def respond(self, context: TutorContext) -> ProviderAnswer:
            raise ProviderUnavailable

    curated = asyncio.run(TutorService(retriever).answer(request))
    assert curated.provider == "curated" and curated.citations[0].kind == "lesson"
    reply = asyncio.run(TutorService(retriever, MockProvider()).answer(request))
    assert reply.provider == "ollama" and reply.citations == curated.citations
    fabricated = asyncio.run(TutorService(retriever, FabricatedProvider()).answer(request))
    unavailable = asyncio.run(TutorService(retriever, UnavailableProvider()).answer(request))
    assert fabricated == unavailable
    assert fabricated.status == "ai_unavailable" and fabricated.citations == curated.citations
    missing = asyncio.run(
        TutorService(retriever, MockProvider()).answer(
            TutorInput(query="zephyr", topic_id="sql.select"),
        )
    )
    assert missing.degraded and missing.status == "no_evidence" and not missing.citations


def test_retrieval_evaluator_requires_the_actual_ground_truth_in_fts(
    indexed_db: tuple[Engine, Content, Catalog], s1: Path
) -> None:
    from app.services.retrieval import Retriever

    from scripts.evaluate_retrieval import Case, QuerySet, evaluate
    from scripts.validate_content import ContentError

    engine, content, _ = indexed_db
    queries = QuerySet(
        review_status="draft",
        cases=[
            Case(id="keys", query="keys", topic_id="relational.keys", expected_lessons=["keys@1"]),
            Case(id="join", query="joins", topic_id="sql.joins", expected_lessons=["joins@1"]),
            Case(
                id="unmatched",
                query="unseen evidence",
                topic_id="sql.joins",
                expected_lessons=["joins@1"],
            ),
        ],
    )
    with pytest.raises(ContentError, match="missing from FTS"):
        evaluate(engine, Retriever(engine, s1), queries, 4)
    with Session(engine) as db, db.begin():
        index_reviewed_lessons(db, content)
    metrics = evaluate(engine, Retriever(engine, s1), queries, 4)
    assert metrics["hit_rate"] == pytest.approx(2 / 3)
    assert metrics["mean_reciprocal_rank"] == pytest.approx(2 / 3)
    assert metrics["label_review_status"] == "draft"
