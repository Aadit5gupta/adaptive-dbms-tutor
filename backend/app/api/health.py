"""Local health endpoint."""

from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


class Health(BaseModel):
    status: Literal["ok"]
    database: Literal["ready"]


def health_router(engine: Engine, required_heads: frozenset[str]) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/health", response_model=Health, responses={503: {"description": "DB unavailable"}}
    )
    def health() -> Health | JSONResponse:
        try:
            with engine.connect() as connection:
                revisions = frozenset(
                    connection.execute(text("SELECT version_num FROM alembic_version")).scalars()
                )
                if revisions == required_heads:
                    return Health(status="ok", database="ready")
        except SQLAlchemyError:
            pass
        return JSONResponse(
            status_code=503,
            content={"detail": "Apply the database migrations and retry.", "code": "db_not_ready"},
        )

    return router
