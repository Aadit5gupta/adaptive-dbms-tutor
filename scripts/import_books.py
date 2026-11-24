"""Publish and index reviewed lessons, or import a cleared UTF-8 book section."""

import argparse
import sys
from pathlib import Path

if __package__ in ("", None):
    project = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(project), str(project / "backend")]

from app.core.config import Settings
from app.core.db import open_engine
from app.core.demo import demo_path
from app.services.curriculum import publish_content
from app.services.source_import import (
    MAX_SECTION_BYTES,
    import_book_section,
    index_bundled_book_excerpts,
    index_reviewed_lessons,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from scripts.validate_content import load_content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "lessons", help="publish curriculum and index reviewed lessons and bundled book excerpts"
    )
    section = commands.add_parser(
        "section", help="import exact section bytes with a matching rights record"
    )
    section.add_argument("--book", required=True)
    section.add_argument("--clearance", required=True)
    section.add_argument("--topic", required=True)
    section.add_argument("--text", required=True, type=Path)
    args = parser.parse_args()

    try:
        settings = Settings()
        engine = open_engine(demo_path(settings) if args.demo else settings.app_db)
        try:
            content = load_content()
            text = None
            if args.command == "section":
                with args.text.open("rb") as file:
                    text = file.read(MAX_SECTION_BYTES + 1)
            with Session(engine) as db, db.begin():
                db.connection().exec_driver_sql("BEGIN IMMEDIATE")
                if text is None:
                    publish_content(db, content)
                    count = index_reviewed_lessons(db, content)
                    count += index_bundled_book_excerpts(db, content)
                else:
                    count = import_book_section(
                        db, content.catalog, args.book, args.clearance, args.topic, text
                    )
        finally:
            engine.dispose()
    except SQLAlchemyError:
        print("Import blocked: check that the configured database is migrated.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Import blocked: {error}", file=sys.stderr)
        return 1
    print(f"Committed {count} searchable passages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
