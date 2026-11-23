"""Reset the two synthetic learners in the dedicated local demo database."""

import sys
from pathlib import Path

if __package__ in ("", None):
    project = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(project), str(project / "backend")]

from app.services.demo import reset_learners

from scripts.demo_support import demo_engine, demo_write


def main() -> None:
    with demo_engine() as engine:
        if engine is None:
            print("No demo database to reset.")
            return
        with demo_write(engine) as db:
            reset_learners(db)
    print("Reset Learners A and B in the dedicated demo database.")


if __name__ == "__main__":
    main()
