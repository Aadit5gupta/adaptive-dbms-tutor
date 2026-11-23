"""ASGI entry point for the local tutor."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.demo import demo_router
from app.api.health import health_router
from app.core.config import PROJECT_ROOT, Settings
from app.core.db import open_engine
from app.core.demo import demo_path
from app.services.assessment import AssessmentError

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    engine = open_engine(config.app_db)
    demo_engine = open_engine(demo_path(config)) if config.demo_enabled else None
    heads = frozenset(ScriptDirectory.from_config(Config(str(ALEMBIC_INI))).get_heads())

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine.dispose()
            if demo_engine is not None:
                demo_engine.dispose()

    app = FastAPI(title="Adaptive DBMS Tutor", lifespan=lifespan)

    @app.exception_handler(AssessmentError)
    async def assessment_error(_: Request, error: AssessmentError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status, content={"detail": str(error), "code": error.code}
        )

    if demo_engine is not None:
        app.include_router(demo_router(demo_engine, PROJECT_ROOT), prefix="/api/v1")
    app.include_router(health_router(engine, heads), prefix="/api/v1")
    return app


app = create_app()
