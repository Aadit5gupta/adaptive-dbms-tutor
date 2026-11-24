"""Read-only catalog and attributed full-text results."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.services.assessment import AssessmentError
from app.services.retrieval import Citation, Retriever, SourceKind, book_counts
from content.schemas.rights import SectionException
from scripts.validate_content import ContentError, load_catalog


class BookView(BaseModel):
    id: str
    title: str
    authors: tuple[str, ...]
    source_url: str
    license: str | None
    license_url: str | None
    license_evidence_url: str
    indexed_sections: int
    searchable_passages: int
    cleared_sections: int
    section_exceptions: tuple[SectionException, ...]


class LibraryView(BaseModel):
    catalog_books: int
    indexed_books: int
    books: list[BookView]


class SearchView(BaseModel):
    citation: Citation
    topic_id: str
    excerpt: str


def library_router(engine: Engine, root: Path) -> APIRouter:
    router = APIRouter(prefix="/library")
    retriever = Retriever(engine, root)

    @router.get("/books", response_model=LibraryView)
    def catalog() -> LibraryView:
        try:
            catalog = load_catalog(root)
            with Session(engine) as db:
                counts = book_counts(db, catalog)
        except (ContentError, SQLAlchemyError) as error:
            raise AssessmentError(
                "The source catalog is unavailable.", "library_unavailable", 503
            ) from error
        books = []
        for book in catalog.books:
            searchable = counts.get(book.id, {})
            books.append(
                BookView(
                    id=book.id,
                    title=book.title,
                    authors=book.authors,
                    source_url=str(book.source_url),
                    license=book.license,
                    license_url=str(book.license_url) if book.license_url else None,
                    license_evidence_url=str(book.license_evidence_url),
                    indexed_sections=len(searchable),
                    searchable_passages=sum(searchable.values()),
                    cleared_sections=sum(section.indexable for section in book.section_clearances),
                    section_exceptions=book.section_exceptions,
                )
            )
        return LibraryView(catalog_books=len(books), indexed_books=len(counts), books=books)

    @router.get("/search", response_model=list[SearchView])
    def search(
        q: Annotated[str, Query(min_length=2, max_length=300)],
        topic: Annotated[str | None, Query(max_length=64)] = None,
        kind: SourceKind | None = None,
    ) -> list[SearchView]:
        try:
            hits = retriever.search(q, (topic,) if topic else (), k=6, kind=kind)
        except (ContentError, SQLAlchemyError) as error:
            raise AssessmentError(
                "Source search is unavailable.", "library_unavailable", 503
            ) from error
        return [
            SearchView(
                citation=hit.citation,
                topic_id=hit.topic_id,
                excerpt=hit.excerpt,
            )
            for hit in hits
        ]

    return router
