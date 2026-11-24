"""Initialize the dedicated demo database with reviewed material and two identities."""

import sys
from pathlib import Path

if __package__ in ("", None):
    project = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(project), str(project / "backend")]

from app.services.curriculum import publish_content
from app.services.demo import seed_learners
from app.services.source_import import index_bundled_book_excerpts, index_reviewed_lessons

from scripts.demo_support import demo_engine, demo_write
from scripts.validate_content import load_content


def main() -> None:
    content = load_content()
    with demo_engine(create=True) as engine:
        assert engine is not None
        with demo_write(engine) as db:
            publish_content(db, content)
            index_reviewed_lessons(db, content)
            index_bundled_book_excerpts(db, content)
            seed_learners(db)
    print(f"Ready: two demo learners, {content.counts.reviewed_mcqs} reviewed MCQs.")
    if not content.counts.reviewed_mcqs:
        print("The browser demo will show an empty state until human review is complete.")


if __name__ == "__main__":
    main()
