"""Shared path guard and transaction setup for the local demo commands."""

from collections.abc import Iterator
from contextlib import contextmanager

from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.core.db import open_engine
from app.core.demo import demo_path, ensure_demo_marker
from app.main import ALEMBIC_INI
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


@contextmanager
def demo_engine(*, create: bool = False) -> Iterator[Engine | None]:
    path = demo_path(Settings())
    if not path.exists() and not create:
        yield None
        return
    engine = open_engine(path, create=create)
    try:
        if create:
            with engine.begin() as db:
                ensure_demo_marker(db)
            config = Config(str(ALEMBIC_INI))
            with engine.begin() as db:
                config.attributes["connection"] = db
                command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()


@contextmanager
def demo_write(engine: Engine) -> Iterator[Session]:
    with Session(engine) as db, db.begin():
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        yield db
