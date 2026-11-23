"""Allow machine-reviewed content while retaining immutable version IDs."""

import sqlite3

import sqlalchemy as sa
from alembic import op

revision = "0007_ai_review"
down_revision = "0006_tutor_threads"
branch_labels = None
depends_on = None

HUMAN = "review_status IN ('author_verified', 'independent_verified')"
LEARNER = "review_status IN ('ai_verified', 'author_verified', 'independent_verified')"
VERSION_TABLES = ("question_versions", "lesson_versions")
QUESTION_COMPONENTS = ("question_options", "sql_exercise_versions")


def replace_constraint(before: str, after: str) -> None:
    db = op.get_bind()
    driver = db.connection.driver_connection
    if not isinstance(driver, sqlite3.Connection):
        raise TypeError("Content migrations require the SQLite driver")
    if not driver.in_transaction:
        db.exec_driver_sql("BEGIN IMMEDIATE")

    # These parents have no cascading foreign keys. Defer checks while their
    # old instances are replaced, then verify the finished schema explicitly.
    db.exec_driver_sql("PRAGMA defer_foreign_keys=ON")
    for table in QUESTION_COMPONENTS:
        op.execute(f"DROP TRIGGER immutable_{table}_insert")
    for table in VERSION_TABLES:
        for event in ("UPDATE", "DELETE"):
            op.execute(f"DROP TRIGGER immutable_{table}_{event.lower()}")
        metadata = sa.MetaData()
        original = sa.Table(table, metadata, autoload_with=db)
        for constraint in list(original.constraints):
            if isinstance(constraint, sa.CheckConstraint) and str(constraint.sqltext) == before:
                original.constraints.remove(constraint)
        with op.batch_alter_table(table, copy_from=original, recreate="always") as batch:
            batch.create_check_constraint(f"{table}_publication_review", after)
        for event in ("UPDATE", "DELETE"):
            op.execute(
                f"CREATE TRIGGER immutable_{table}_{event.lower()} BEFORE {event} ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'Published content is immutable'); END"
            )
    for table in QUESTION_COMPONENTS:
        op.execute(
            f"CREATE TRIGGER immutable_{table}_insert BEFORE INSERT ON {table} "
            "WHEN EXISTS (SELECT 1 FROM question_versions WHERE id = NEW.question_version_id) "
            "BEGIN SELECT RAISE(ABORT, 'Published content is immutable'); END"
        )
    if db.exec_driver_sql("PRAGMA foreign_key_check").first() is not None:
        raise RuntimeError("Foreign key check failed after content migration")
    # SQLite retains deferred counters for the dropped instances even after
    # valid replacements. The explicit check above covers the final graph.
    db.exec_driver_sql("PRAGMA defer_foreign_keys=OFF")


def upgrade() -> None:
    replace_constraint(HUMAN, LEARNER)


def downgrade() -> None:
    replace_constraint(LEARNER, HUMAN)
