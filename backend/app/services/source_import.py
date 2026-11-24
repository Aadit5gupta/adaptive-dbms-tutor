"""Index reviewed lessons and hash-matched, approved book sections."""

import re
from hashlib import sha256

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.db.models import LessonVersion, Passage, Topic
from content.schemas.models import Lesson
from content.schemas.rights import Catalog
from scripts.validate_content import Content

MAX_SECTION_BYTES = 2_000_000
CHUNK_WORDS = 320
MIN_REMAINDER = 80
WORD = re.compile(r"[\w]+", re.UNICODE)


def chunk_text(text: str) -> list[str]:
    words = text.split()
    result: list[str] = []
    for start in range(0, len(words), CHUNK_WORDS):
        part = " ".join(words[start : start + CHUNK_WORDS])
        if len(words) - start < MIN_REMAINDER and result:
            result[-1] += f" {part}"
        elif WORD.search(part):
            result.append(part)
    return result


def index_reviewed_lessons(db: Session, content: Content) -> int:
    # Independently authored lessons retain their own attribution and keep book counts separate.
    latest: dict[str, Lesson] = {}
    for item in content.lessons.values():
        if (
            item.reviewed
            and item.source.kind == "authored"
            and item.source.source_section_clearance_id is None
            and (item.id not in latest or item.version > latest[item.id].version)
        ):
            latest[item.id] = item
    db.execute(
        delete(Passage).where(
            Passage.kind == "lesson",
            Passage.lesson_ref.not_in([item.ref for item in latest.values()]),
        )
    )
    count = 0
    for item in latest.values():
        if db.get(LessonVersion, item.ref) is None:
            raise ValueError(f"{item.ref}: publish the reviewed version before indexing")
        review = (
            "AI-verified original lesson"
            if item.review_status == "ai_verified"
            else "Human-reviewed lesson"
        )
        text = item.body_markdown
        digest = sha256(text.encode("utf-8")).hexdigest()
        for number, body in enumerate(chunk_text(text), 1):
            db.execute(
                insert(Passage)
                .values(
                    passage_key=f"{item.ref}#{number}",
                    kind="lesson",
                    lesson_ref=item.ref,
                    topic_id=item.subtopic_id,
                    title=item.title,
                    body=body,
                    source_url=str(item.source.factual_reference_url),
                    attribution=f"{review} by {item.author}",
                    source_hash=digest,
                )
                .on_conflict_do_nothing(index_elements=["passage_key"])
            )
            count += 1
    return count


def import_book_section(
    db: Session,
    catalog: Catalog,
    book_id: str,
    clearance_id: str,
    topic_id: str,
    section_bytes: bytes,
) -> int:
    if len(section_bytes) > MAX_SECTION_BYTES:
        raise ValueError("section exceeds the two-megabyte import limit")
    clearance = catalog.verify_import(book_id, clearance_id, section_bytes)
    if db.get(Topic, topic_id) is None:
        raise ValueError(f"{topic_id}: unknown curriculum topic")
    book = next(book for book in catalog.books if book.id == book_id)
    chunks = chunk_text(section_bytes.decode("utf-8"))
    if not chunks:
        raise ValueError("approved text has no searchable passage")

    rows = list(
        db.scalars(
            select(Passage).where(Passage.kind == "book", Passage.clearance_id == clearance_id)
        )
    )
    if len(rows) == len(chunks) and all(
        row.book_id == book_id
        and row.source_hash == clearance.approved_content_hash
        and row.topic_id == topic_id
        and row.source_url == str(clearance.section_url)
        and row.license_url == str(clearance.license_url)
        and row.attribution == clearance.attribution_text
        for row in rows
    ):
        return len(rows)

    db.execute(delete(Passage).where(Passage.kind == "book", Passage.clearance_id == clearance_id))
    db.add_all(
        Passage(
            passage_key=f"{book_id}:{clearance_id}:{clearance.approved_content_hash[:16]}#{number}",
            kind="book",
            book_id=book_id,
            clearance_id=clearance_id,
            topic_id=topic_id,
            title=book.title,
            body=body,
            source_url=str(clearance.section_url),
            license_url=str(clearance.license_url),
            attribution=clearance.attribution_text,
            source_hash=clearance.approved_content_hash,
        )
        for number, body in enumerate(chunks, 1)
    )
    db.flush()
    return len(chunks)



def index_bundled_book_excerpts(db: Session, content: Content) -> int:
    return sum(
        import_book_section(
            db, content.catalog, excerpt.book_id, excerpt.clearance_id, excerpt.topic_id, excerpt.text
        )
        for excerpt in content.book_excerpts
    )
