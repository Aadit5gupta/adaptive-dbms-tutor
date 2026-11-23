"""Apply Alembic revisions to the configured application database."""

from typing import Any

from alembic import context
from app.core.config import Settings
from app.core.db import open_engine
from app.core.demo import demo_path, ensure_demo_marker
from app.db.models import Base
from sqlalchemy.engine import Connection


def include_name(name: str | None, type_: str, _: Any) -> bool:
    return type_ != "table" or name is None or not name.startswith("source_passages_fts")


def run_migrations() -> None:
    existing = context.config.attributes.get("connection")
    if isinstance(existing, Connection):
        context.configure(
            connection=existing, target_metadata=Base.metadata, include_name=include_name
        )
        with context.begin_transaction():
            context.run_migrations()
        return
    settings = Settings()
    demo = context.get_x_argument(as_dictionary=True).get("demo") == "true"
    path = demo_path(settings) if demo else settings.app_db
    if context.is_offline_mode():
        context.configure(
            dialect_name="sqlite",
            literal_binds=True,
            target_metadata=Base.metadata,
            include_name=include_name,
        )
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = open_engine(path, create=True)
    try:
        with engine.connect() as connection:
            if demo:
                ensure_demo_marker(connection)
                connection.commit()
            context.configure(
                connection=connection, target_metadata=Base.metadata, include_name=include_name
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
