"""ASGI entry point for the local tutor."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI

from app.api.health import health_router
from app.core.config import Settings
from app.core.db import open_engine

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    engine = open_engine(config.app_db)
    heads = frozenset(ScriptDirectory.from_config(Config(str(ALEMBIC_INI))).get_heads())

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Adaptive DBMS Tutor", lifespan=lifespan)
    app.include_router(health_router(engine, heads), prefix="/api/v1")
    return app


app = create_app()
