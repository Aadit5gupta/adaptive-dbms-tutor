"""Dedicated demo database identity and synthetic learner rows."""

import sqlite3
from contextlib import closing
from pathlib import Path

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Connection

from app.core.config import PROJECT_ROOT, Settings
from app.db.models import User

DEFAULT_DEMO_DB = PROJECT_ROOT / "data/demo.sqlite"
DEMO_APPLICATION_ID = 0x44424D53
DEMO_LEARNERS = {"a": "demo-learner-a", "b": "demo-learner-b"}


def demo_path(settings: Settings, approved_path: Path = DEFAULT_DEMO_DB) -> Path:
    """Enforce the literal allowlist path and refuse unmarked existing files."""
    path = settings.demo_db
    if path != approved_path or path.resolve() != approved_path or path == settings.app_db:
        raise ValueError("expected the dedicated allowlisted demo database")
    if path.exists():
        with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)) as db:
            marker = db.execute("PRAGMA application_id").fetchone()[0]
        if marker != DEMO_APPLICATION_ID:
            raise ValueError("existing database is missing the demo marker")
    return path


def ensure_demo_marker(connection: Connection) -> None:
    marker = connection.exec_driver_sql("PRAGMA application_id").scalar_one()
    if marker == DEMO_APPLICATION_ID:
        return
    tables = connection.exec_driver_sql(
        "SELECT name FROM sqlite_schema WHERE type = 'table' LIMIT 1"
    ).first()
    if marker != 0 or tables is not None:
        raise ValueError("demo marker may only be added to a fresh database")
    connection.exec_driver_sql(f"PRAGMA application_id = {DEMO_APPLICATION_ID}")


def seed_demo_users(connection: Connection) -> None:
    if connection.exec_driver_sql("PRAGMA application_id").scalar_one() != DEMO_APPLICATION_ID:
        raise ValueError("synthetic learner identities require the demo database")
    for learner_id in DEMO_LEARNERS.values():
        connection.execute(
            insert(User)
            .values(id=learner_id, is_demo=True, created_at=0)
            .on_conflict_do_nothing(index_elements=["id"])
        )
