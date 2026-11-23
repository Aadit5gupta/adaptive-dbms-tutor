"""ASGI entry point for the local tutor."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.api.accounts import account_router
from app.api.demo import demo_router
from app.api.health import health_router
from app.api.learning import learning_router
from app.api.library import library_router
from app.api.tutor import local_tutor_router, tutor_router
from app.core.auth import Accounts
from app.core.config import PROJECT_ROOT, Settings
from app.core.db import open_engine
from app.core.demo import demo_path
from app.core.origin import SAFE, allowed_origin
from app.providers.ollama import OllamaProvider
from app.services.assessment import AssessmentError
from app.services.retrieval import Retriever
from app.services.tutor import TutorService

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def create_app(settings: Settings | None = None, *, content_root: Path = PROJECT_ROOT) -> FastAPI:
    config = settings or Settings()
    engine = open_engine(config.app_db)
    demo_engine = open_engine(demo_path(config)) if config.demo_enabled else None
    provider = (
        OllamaProvider(config.ollama_base_url, config.ollama_model)
        if config.tutor_provider == "ollama"
        else None
    )
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

    @app.middleware("http")
    async def protect_mutations(request: Request, call_next: RequestResponseEndpoint) -> Response:
        if (
            request.method not in SAFE
            and request.url.path.startswith("/api/v1/")
            and not allowed_origin(request, config.allowed_origins)
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "The request origin is not allowed.", "code": "invalid_origin"},
            )
        response = await call_next(request)
        if request.url.path.startswith("/api/v1/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, error: RequestValidationError) -> JSONResponse:
        fields = [".".join(map(str, field["loc"])) for field in error.errors()]
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Check the request fields and try again.",
                "code": "invalid_request",
                "fields": fields,
            },
        )

    @app.exception_handler(AssessmentError)
    async def assessment_error(_: Request, error: AssessmentError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status, content={"detail": str(error), "code": error.code}
        )

    if demo_engine is not None:
        app.include_router(demo_router(demo_engine, content_root), prefix="/api/v1")
        app.include_router(
            local_tutor_router(
                TutorService(Retriever(demo_engine, content_root), provider), demo_engine
            ),
            prefix="/api/v1",
        )
    accounts = Accounts(engine, secure_cookie=config.secure_cookies)
    app.include_router(account_router(accounts), prefix="/api/v1")
    app.include_router(learning_router(accounts, content_root), prefix="/api/v1")
    app.include_router(
        tutor_router(
            TutorService(Retriever(engine, content_root), provider), engine, accounts.require_user
        ),
        prefix="/api/v1",
    )
    app.include_router(library_router(engine, content_root), prefix="/api/v1")
    app.include_router(health_router(engine, heads), prefix="/api/v1")
    return app


app = create_app()
