"""Replay the learner A/B demo against a disposable copy of the marked database."""

import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

if __package__ in ("", None):
    project = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(project), str(project / "backend")]

from app.core.db import open_engine
from app.db.models import SQLExerciseVersion
from app.schemas.assessment import AnswerInput, SQLAnswerInput
from app.services.assessment import options_for, submit_mcq, submit_sql
from app.services.demo import (
    Learner,
    demo_state,
    recommended_lesson,
    require_learner,
    reset_learners,
    seed_learners,
    start_activity,
)
from sqlalchemy.orm import Session

from scripts.demo_support import demo_engine, demo_write
from scripts.validate_content import ROOT, ContentError, check_stage, load_content


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContentError(message)


def replay(path: Path, content_root: Path) -> None:
    engine = open_engine(path)
    learners: tuple[Learner, ...] = ("a", "b")
    try:
        with demo_write(engine) as db:
            reset_learners(db)
            seed_learners(db)
        for learner in learners:
            code = "KEYS-02" if learner == "a" else "SQL-JOIN-01"
            for pool in ("diagnostic", "practice"):
                with demo_write(engine) as db:
                    user = require_learner(db, learner)
                    session = start_activity(db, learner, pool)
                    item = session.items[0]
                    option = next(
                        (
                            row
                            for row in options_for(db, item.question_ref)
                            if row.misconception_code == code
                        ),
                        None,
                    )
                    if option is None:
                        raise ContentError(f"{item.question_ref}: no mapped demo distractor")
                    index = option.option_index
                result = submit_mcq(
                    engine,
                    user,
                    session.session_id,
                    f"{learner}-{pool}",
                    AnswerInput(item_id=item.item_id, option_index=index),
                )
                require(
                    not result.correct,
                    f"Learner {learner} should receive deterministic wrong-answer feedback",
                )
            with demo_write(engine) as db:
                detected = demo_state(db, learner)
                require(
                    any(h.code == code and h.state == "active" for h in detected.hypotheses),
                    f"Learner {learner} should have an active {code} hypothesis",
                )
                require(recommended_lesson(db, learner).title != "", "Expected an approved lesson")
                checks = start_activity(db, learner, "checkpoint")
                correct = [
                    next(
                        option.option_index
                        for option in options_for(db, item.question_ref)
                        if option.is_correct
                    )
                    for item in checks.items
                ]
            require(len(correct) == 2, "Expected two reserved checkpoints")
            for item, index in zip(checks.items, correct, strict=True):
                submit_mcq(
                    engine,
                    user,
                    checks.session_id,
                    item.question_ref,
                    AnswerInput(item_id=item.item_id, option_index=index),
                )
            with Session(engine) as db:
                after = demo_state(db, learner)
                require(
                    any(h.code == code and h.state == "resolved" for h in after.hypotheses),
                    f"Learner {learner} should resolve {code}",
                )
                require(
                    after.recommendation != detected.recommendation, "Recommendation should change"
                )

        with demo_write(engine) as db:
            sql = start_activity(db, "b", "sql")
            sql_item = sql.items[0]
            exercise = db.get(SQLExerciseVersion, sql_item.question_ref)
            assert exercise is not None
            query = exercise.reference_query
            user = require_learner(db, "b")
        result = submit_sql(
            engine,
            content_root,
            user,
            sql.session_id,
            "demo-sql",
            SQLAnswerInput(item_id=sql_item.item_id, query=query),
        )
        require(result.correct, "Reference query should pass the demo SQL exercise")
    finally:
        engine.dispose()


def main() -> int:
    try:
        check_stage(load_content().counts, "S1")
        with demo_engine() as engine, TemporaryDirectory(prefix="dbms-demo-verify-") as directory:
            if engine is None:
                raise ContentError("Seed the dedicated demo database first.")
            clone = Path(directory) / "demo.sqlite"
            with engine.connect() as connection, closing(sqlite3.connect(clone)) as copy:
                native = connection.connection.driver_connection
                if not isinstance(native, sqlite3.Connection):
                    raise ContentError("Unexpected database driver")
                native.backup(copy)
            replay(clone, ROOT)
    except ValueError as error:
        print(f"Demo verification blocked: {error}")
        return 1
    print("Verified two learners, independent hypotheses, checkpoint resolution and SQL grading.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
