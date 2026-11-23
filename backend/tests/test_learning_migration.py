from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.core.db import open_engine
from app.core.demo import DEMO_LEARNERS, demo_path, ensure_demo_marker, seed_demo_users
from app.main import ALEMBIC_INI
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

PUBLISH = """
INSERT INTO question_versions VALUES (
    :ref, 'question', :version, 'practice', 'Stem', 'easy', 'Explanation',
    'author_verified', 'Source', 'Synthetic test author', '2026-11-23', 'hash'
)
"""


@pytest.fixture
def migrated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("DBMS_APP_DB", str(tmp_path / "app.sqlite"))
    monkeypatch.setenv("DBMS_DEMO_DB", str(tmp_path / "demo.sqlite"))
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    return Settings()


def test_published_versions_are_immutable(migrated: Settings) -> None:
    engine = open_engine(migrated.app_db)
    try:
        with engine.begin() as db:
            db.execute(text("INSERT INTO topics VALUES ('sql.select', 'sql', 'SELECT', 0)"))
            db.execute(text("INSERT INTO questions VALUES ('question', 'sql.select', 'mcq')"))
            db.execute(
                text("INSERT INTO question_options VALUES ('question@1', 0, 'Choice', 1, NULL)")
            )
            db.execute(text(PUBLISH), {"ref": "question@1", "version": 1})

        commands = [
            "UPDATE question_versions SET stem = 'New' WHERE id = 'question@1'",
            "DELETE FROM question_versions WHERE id = 'question@1'",
            "UPDATE question_options SET body = 'Other' WHERE question_version_id = 'question@1'",
            "INSERT INTO question_options VALUES ('question@1', 1, 'Other', 0, NULL)",
        ]
        for statement in commands:
            with pytest.raises(IntegrityError, match="immutable"), engine.begin() as db:
                db.execute(text(statement))
        with pytest.raises(IntegrityError, match="immutable"), engine.begin() as db:
            db.execute(
                text(PUBLISH.replace("INSERT", "INSERT OR REPLACE", 1)),
                {"ref": "question@1", "version": 1},
            )

        with engine.begin() as db:
            db.execute(text(PUBLISH), {"ref": "question@2", "version": 2})
            assert db.scalar(text("SELECT COUNT(*) FROM question_versions")) == 2
    finally:
        engine.dispose()


def test_foreign_keys_reject_missing_content(migrated: Settings) -> None:
    engine = open_engine(migrated.app_db)
    try:
        with pytest.raises(IntegrityError, match="FOREIGN KEY"), engine.begin() as db:
            db.execute(text("INSERT INTO questions VALUES ('question', 'unknown.topic', 'mcq')"))
        with pytest.raises(IntegrityError, match="FOREIGN KEY"), engine.begin() as db:
            db.execute(
                text("INSERT INTO question_options VALUES ('missing@1', 0, 'Choice', 1, NULL)")
            )
    finally:
        engine.dispose()


def test_demo_marker_and_identities_are_isolated(migrated: Settings, tmp_path: Path) -> None:
    demo = demo_path(migrated, tmp_path / "demo.sqlite")
    regular_engine = open_engine(migrated.app_db)
    demo_engine = open_engine(demo, create=True)
    try:
        with regular_engine.begin() as db:
            with pytest.raises(ValueError, match="require the demo database"):
                seed_demo_users(db)
            with pytest.raises(ValueError, match="fresh database"):
                ensure_demo_marker(db)
        with demo_engine.begin() as db:
            ensure_demo_marker(db)
        with demo_engine.begin() as db:
            # Copy the schema through a real migration pointed at the isolated test database.
            config = Config(str(ALEMBIC_INI))
            config.attributes["connection"] = db
            command.upgrade(config, "head")
            seed_demo_users(db)
            seed_demo_users(db)
            assert set(db.scalars(text("SELECT id FROM users WHERE is_demo")).all()) == set(
                DEMO_LEARNERS.values()
            )
        assert demo_path(migrated, demo) == demo
        with regular_engine.connect() as db:
            assert db.scalar(text("SELECT COUNT(*) FROM users")) == 0
    finally:
        demo_engine.dispose()
        regular_engine.dispose()


def test_attempt_uniqueness_and_item_version(migrated: Settings) -> None:
    engine = open_engine(migrated.app_db)
    insert_attempt = text("""
        INSERT INTO attempts (
            id, user_id, session_item_id, question_version_id, idempotency_key,
            request_fingerprint, result_json, correct, hint_used, context, created_at
        ) VALUES (:id, 'u', :item, :version, :key, 'request', '{}', 1, 0, 'practice', 0)
        """)
    try:
        with engine.begin() as db:
            db.exec_driver_sql("INSERT INTO users (id, is_demo, created_at) VALUES ('u', 0, 0)")
            db.exec_driver_sql("INSERT INTO topics VALUES ('sql.select', 'sql', 'SELECT', 0)")
            db.exec_driver_sql("INSERT INTO questions VALUES ('question', 'sql.select', 'mcq')")
            for number in (1, 2):
                db.execute(text(PUBLISH), {"ref": f"question@{number}", "version": number})
            db.exec_driver_sql(
                "INSERT INTO assessment_sessions VALUES ('s', 'u', 'practice', 'open', 0, NULL)"
            )
            for number in (1, 2):
                db.execute(
                    text("""
                    INSERT INTO assessment_session_items
                        (id, session_id, question_version_id, position, status, revealing_hint_used, remediation_code) VALUES (:item, 's', 'question@1', :pos,
                        'open', 0, NULL)
                    """),
                    {"item": f"i{number}", "pos": number},
                )
            db.execute(
                insert_attempt, {"id": "a1", "item": "i1", "version": "question@1", "key": "one"}
            )
        for item, version, key, constraint in (
            ("i1", "question@1", "two", "attempts.session_item_id"),
            ("i2", "question@1", "one", "attempts.user_id, attempts.idempotency_key"),
            ("i2", "question@2", "two", "FOREIGN KEY"),
        ):
            with pytest.raises(IntegrityError, match=constraint), engine.begin() as db:
                db.execute(
                    insert_attempt, {"id": "a2", "item": item, "version": version, "key": key}
                )
    finally:
        engine.dispose()
