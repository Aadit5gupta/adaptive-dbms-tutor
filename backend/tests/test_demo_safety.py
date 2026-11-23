import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.core.db import open_engine
from app.core.demo import DEMO_LEARNERS, demo_path, ensure_demo_marker
from app.db.models import User
from app.main import ALEMBIC_INI
from app.services.curriculum import publish_from_disk
from app.services.demo import reset_learners, seed_learners
from app.services.sql_grading import worker_supported
from sqlalchemy.orm import Session

from scripts.demo_support import demo_write
from scripts.verify_demo import replay


def test_reset_preserves_regular_db_and_non_demo_rows(tmp_path: Path) -> None:
    settings = Settings(app_db=tmp_path / "app.sqlite", demo_db=tmp_path / "demo.sqlite")
    with closing(sqlite3.connect(settings.app_db)) as regular:
        regular.execute("CREATE TABLE sentinel(i INTEGER)")
        regular.commit()
    before = sha256(settings.app_db.read_bytes()).digest()
    cfg = Config(str(ALEMBIC_INI))
    engine = open_engine(demo_path(settings, settings.demo_db), create=True)
    try:
        with engine.begin() as connection:
            ensure_demo_marker(connection)
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        with demo_write(engine) as db:
            seed_learners(db)
            db.add(User(id="regular-user", is_demo=False, created_at=1))
        with demo_write(engine) as db:
            reset_learners(db)
        with Session(engine) as db:
            assert db.get(User, "regular-user") is not None
            for user in DEMO_LEARNERS.values():
                assert db.get(User, user) is None
    finally:
        engine.dispose()
    assert sha256(settings.app_db.read_bytes()).digest() == before


def test_demo_guard_rejects_an_existing_unmarked_file(tmp_path: Path) -> None:
    settings = Settings(app_db=tmp_path / "app.sqlite", demo_db=tmp_path / "demo.sqlite")
    with closing(sqlite3.connect(settings.demo_db)) as regular:
        regular.execute("CREATE TABLE sentinel(i INTEGER)")
    with pytest.raises(ValueError, match="missing the demo marker"):
        demo_path(settings, settings.demo_db)


@pytest.mark.skipif(not worker_supported(), reason="SQL worker is disabled on this platform")
def test_demo_replay_with_synthetic_verified_fixture(s1: Path) -> None:
    demo = s1 / "demo.sqlite"
    cfg = Config(str(ALEMBIC_INI))
    engine = open_engine(demo, create=True)
    try:
        with engine.begin() as connection:
            ensure_demo_marker(connection)
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        with demo_write(engine) as db:
            publish_from_disk(db, s1)
    finally:
        engine.dispose()
    replay(demo, s1)
