"""Publisher catalog and explicit per-section local indexing approvals."""

from datetime import date
from hashlib import sha256
from typing import Annotated, Literal
from urllib.parse import unquote

from pydantic import Field, HttpUrl, StringConstraints, model_validator

from content.schemas.models import LogicalId, Record, Text

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
CATALOG_IDS = {
    "bccampus_db_design_2e",
    "runestone_practical_db",
    "shea_pop_culture_sql",
    "openstax_foundations_is",
    "datafield_db_fundamentals",
}
BCCAMPUS_EXCEPTIONS = {
    "chapter-10-er-modelling": "https://creativecommons.org/licenses/by/3.0/",
    "chapter-11-functional-dependencies": "https://creativecommons.org/licenses/by-sa/3.0/",
}


class SectionException(Record):
    section_url: HttpUrl
    issue: Text
    other_license_url: HttpUrl | None = None
    status: Literal[
        "link_only", "blocked_pending_review", "blocked_pending_permission", "excluded_image"
    ]
    accessed_on: date


class Clearance(Record):
    id: LogicalId
    section_url: HttpUrl
    license_url: HttpUrl
    rights_status: Literal[
        "link_only", "approved_local_index", "blocked_pending_review", "blocked_pending_permission"
    ]
    scope: Literal["text_only"]
    exceptions_found: Text
    exceptions_resolved: bool = False
    accessed_on: date
    reviewer: Text
    reviewed_on: date
    approved_content_hash: Sha256
    attribution_text: Text
    permission_evidence_url: HttpUrl | None = None

    @model_validator(mode="after")
    def check_dates(self) -> "Clearance":
        if self.reviewed_on < self.accessed_on:
            raise ValueError("reviewed_on precedes accessed_on")
        return self


class Book(Record):
    id: LogicalId
    title: Text
    authors: Annotated[tuple[Text, ...], Field(min_length=1)]
    source_url: HttpUrl
    license: Text | None
    license_url: HttpUrl | None
    license_evidence_url: HttpUrl
    accessed_on: date
    section_exceptions: tuple[SectionException, ...]
    section_clearances: tuple[Clearance, ...]
    notes: Text
    default_import_policy: Literal["link_only"]


def section_path(url: HttpUrl) -> str:
    return unquote(url.path or "/").rstrip("/")


class Catalog(Record):
    schema_version: Literal[2]
    book_license_verification_date: date
    notice: Text
    books: tuple[Book, ...]

    @property
    def approved_clearances(self) -> dict[str, Clearance]:
        return {
            clearance.id: clearance
            for book in self.books
            for clearance in book.section_clearances
            if clearance.rights_status == "approved_local_index"
        }

    @model_validator(mode="after")
    def check_catalog(self) -> "Catalog":
        if len(self.books) != len(CATALOG_IDS) or {book.id for book in self.books} != CATALOG_IDS:
            raise ValueError("expected five unique canonical catalog book IDs")

        clearance_ids: set[str] = set()
        for book in self.books:
            self.check_exceptions(book)
            urls: set[str] = set()
            for clearance in book.section_clearances:
                if clearance.id in clearance_ids or str(clearance.section_url) in urls:
                    raise ValueError(f"{book.id}: duplicate clearance ID or section URL")
                clearance_ids.add(clearance.id)
                urls.add(str(clearance.section_url))
                if clearance.rights_status == "approved_local_index":
                    self.check_approval(book, clearance)
        return self

    @staticmethod
    def check_exceptions(book: Book) -> None:
        if book.id != "bccampus_db_design_2e":
            return
        for chapter, license_url in BCCAMPUS_EXCEPTIONS.items():
            if not any(
                section_path(exception.section_url).endswith("/" + chapter)
                and str(exception.other_license_url) == license_url
                and exception.status == "blocked_pending_review"
                for exception in book.section_exceptions
            ):
                raise ValueError(f"{book.id}: missing required exception for {chapter}")

    @staticmethod
    def check_approval(book: Book, clearance: Clearance) -> None:
        if clearance.section_url.host != book.source_url.host:
            raise ValueError(f"{clearance.id}: section URL is outside book host")
        if clearance.exceptions_found.casefold() != "none" and not clearance.exceptions_resolved:
            raise ValueError(f"{clearance.id}: section exceptions must be resolved")
        if clearance.reviewer.lower().startswith("ai:"):
            raise ValueError(f"{clearance.id}: section clearance requires a human reviewer")
        if book.id == "openstax_foundations_is" and not clearance.permission_evidence_url:
            raise ValueError("OpenStax tutor ingestion requires documented written permission")
        if book.id == "datafield_db_fundamentals" and not clearance.permission_evidence_url:
            raise ValueError("DataField remains link-only without documented permission")
        if book.id == "bccampus_db_design_2e":
            for chapter, license_url in BCCAMPUS_EXCEPTIONS.items():
                if chapter in section_path(clearance.section_url).casefold().split("/") and (
                    not clearance.exceptions_resolved
                    or str(clearance.license_url) != license_url
                    or clearance.exceptions_found.casefold() == "none"
                ):
                    raise ValueError(
                        f"{chapter}: separately reviewed derivative clearance required"
                    )
        for exception in book.section_exceptions:
            if (
                exception.status in {"blocked_pending_review", "blocked_pending_permission"}
                and exception.section_url.host == clearance.section_url.host
                and section_path(exception.section_url) == section_path(clearance.section_url)
                and not clearance.exceptions_resolved
            ):
                raise ValueError(f"{clearance.id}: recorded section exception must be resolved")

    def verify_import(self, book_id: str, clearance_id: str, text: bytes) -> Clearance:
        """Return attribution only for exact approved UTF-8 text bytes."""
        for book in self.books:
            if book.id != book_id:
                continue
            for clearance in book.section_clearances:
                if (
                    clearance.id == clearance_id
                    and clearance.rights_status == "approved_local_index"
                ):
                    if sha256(text).hexdigest() != clearance.approved_content_hash:
                        raise ValueError(f"{clearance_id}: approved content hash mismatch")
                    if not text.decode("utf-8").strip():
                        raise ValueError(f"{clearance_id}: section text is empty")
                    return clearance
        raise ValueError(f"{book_id}/{clearance_id}: no approval to index section")
