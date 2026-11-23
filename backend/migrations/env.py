"""Apply Alembic revisions to the configured application database."""

from alembic import context
from app.core.config import Settings
from app.core.db import open_engine


def run_migrations() -> None:
    path = Settings().app_db
    if context.is_offline_mode():
        context.configure(dialect_name="sqlite", literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = open_engine(path, create=True)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
