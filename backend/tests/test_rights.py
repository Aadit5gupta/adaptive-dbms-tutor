from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from content.schemas.rights import Catalog
from scripts.validate_content import ROOT, ContentError, load_book_excerpts, read_yaml

TEXT = b"Original synthetic text for the clearance test."


@pytest.fixture
def manifest() -> dict[str, Any]:
    return dict(read_yaml(ROOT / "content/manifests/books.yaml"))


def clearance(url: str) -> dict[str, Any]:
    return {
        "id": "synthetic_clearance",
        "section_url": url,
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "rights_status": "approved_local_index",
        "scope": "text_only",
        "exceptions_found": "none",
        "accessed_on": "2026-11-22",
        "reviewer": "Synthetic rights reviewer",
        "reviewed_on": "2026-11-23",
        "approved_content_hash": sha256(TEXT).hexdigest(),
        "attribution_text": "Synthetic test attribution",
    }


def test_catalog_has_four_publisher_records_and_no_blanket_approval(
    manifest: dict[str, Any],
) -> None:
    catalog = Catalog.model_validate(manifest)
    assert len(catalog.books) == 5
    assert catalog.approved_clearances.keys() == {
        "bccampus_orphan_records",
        "datafield_transaction_atomicity",
        "runestone_foreign_key_actions",
        "shea_sqlite_index_storage",
    }
    assert all(
        item.rights_status == "publisher_license_verified" and item.reviewer.startswith("ai:")
        for item in catalog.approved_clearances.values()
    )
    with pytest.raises(ValueError, match="no approval"):
        catalog.verify_import("bccampus_db_design_2e", "missing", TEXT)


@pytest.mark.parametrize("duplicate", [False, True])
def test_requires_all_unique_books(manifest: dict[str, Any], duplicate: bool) -> None:
    manifest["books"].pop()
    if duplicate:
        manifest["books"].append(deepcopy(manifest["books"][0]))
    with pytest.raises(ValidationError, match="five unique canonical"):
        Catalog.model_validate(manifest)


def test_verified_import_checks_book_and_unchanged_bytes(manifest: dict[str, Any]) -> None:
    book = manifest["books"][0]
    approval = clearance("https://opentextbc.ca/dbdesign01/chapter/test/")
    book["section_clearances"] = [approval]
    catalog = Catalog.model_validate(manifest)
    assert catalog.verify_import(book["id"], approval["id"], TEXT).attribution_text
    with pytest.raises(ValueError, match="hash mismatch"):
        catalog.verify_import(book["id"], approval["id"], TEXT + b"\n")
    with pytest.raises(ValueError, match="no approval"):
        catalog.verify_import("runestone_practical_db", approval["id"], TEXT)


def test_datafield_requires_permission(manifest: dict[str, Any]) -> None:
    manifest["books"][-1]["section_clearances"] = [clearance("https://datafield.dev/sql/test/")]
    with pytest.raises(
        ValidationError, match="Other DataField sections require documented permission"
    ):
        Catalog.model_validate(manifest)


@pytest.mark.parametrize(
    "section", ["chapter-10-er-modelling", "chapter-11-functional-dependencies"]
)
def test_bccampus_requires_separate_derivative_review(
    manifest: dict[str, Any], section: str
) -> None:
    manifest["books"][0]["section_clearances"] = [
        clearance(f"https://opentextbc.ca/dbdesign01/chapter/{section}/#example")
    ]
    with pytest.raises(ValidationError, match="separately reviewed derivative"):
        Catalog.model_validate(manifest)


def test_unknown_rights_status_is_rejected(manifest: dict[str, Any]) -> None:
    manifest["books"][0]["default_import_policy"] = "indexed"
    with pytest.raises(ValidationError, match="link_only"):
        Catalog.model_validate(manifest)


def test_invalid_approval_does_not_index(manifest: dict[str, Any]) -> None:
    approval = clearance("https://opentextbc.ca/dbdesign01/chapter/test/")
    approval["exceptions_found"] = "Third-party text"
    manifest["books"][0]["section_clearances"] = [approval]
    with pytest.raises(ValidationError, match="exceptions must be resolved"):
        Catalog.model_validate(manifest)


def test_openstax_tutor_ingestion_requires_written_permission(manifest: dict[str, Any]) -> None:
    book = next(book for book in manifest["books"] if book["id"] == "openstax_foundations_is")
    section = next(
        exception["section_url"]
        for exception in book["section_exceptions"]
        if exception["status"] == "blocked_pending_permission"
    )
    approval = clearance(section)
    approval.update(exceptions_found="Publisher AI-use notice", exceptions_resolved=True)
    book["section_clearances"] = [approval]
    with pytest.raises(ValidationError, match="OpenStax tutor ingestion requires"):
        Catalog.model_validate(manifest)


def test_ai_cannot_serve_as_rights_reviewer(manifest: dict[str, Any]) -> None:
    approval = clearance("https://opentextbc.ca/dbdesign01/chapter/test/")
    approval["reviewer"] = "ai:reviewer"
    manifest["books"][0]["section_clearances"] = [approval]
    with pytest.raises(ValidationError, match="requires a human reviewer"):
        Catalog.model_validate(manifest)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("section_url", "https://opentextbc.ca/dbdesign01/chapter/other/", "outside verified"),
        ("license_url", "https://creativecommons.org/licenses/by-sa/4.0/", "outside verified"),
        ("reviewer", "Synthetic human reviewer", "explicit AI reviewer"),
        ("exceptions_found", "Third-party excerpt", "exceptions must be resolved"),
    ],
)
def test_publisher_records_cannot_expand_scope(
    manifest: dict[str, Any], field: str, value: str, message: str
) -> None:
    manifest["books"][0]["section_clearances"][0][field] = value
    with pytest.raises(ValidationError, match=message):
        Catalog.model_validate(manifest)


def test_bundled_text_rejects_changed_bytes(manifest: dict[str, Any], tmp_path: Path) -> None:
    catalog = Catalog.model_validate(manifest)
    source = tmp_path / "content/manifests/book_excerpts/bccampus_orphan_records.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(TEXT)
    with pytest.raises(ContentError, match="approved content hash mismatch"):
        load_book_excerpts(tmp_path, catalog, {"relational.keys"})
