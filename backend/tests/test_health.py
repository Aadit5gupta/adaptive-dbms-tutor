import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.core.db import open_engine
from app.main import ALEMBIC_INI, create_app
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import text


def test_health_requires_current_migration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app_path = tmp_path / "with spaces" / "app.sqlite"
    demo_path = tmp_path / "demo.sqlite"
    monkeypatch.setenv("DBMS_APP_DB", str(app_path))
    monkeypatch.setenv("DBMS_DEMO_DB", str(demo_path))
    settings = Settings()
    app = create_app(settings)

    async def check_readiness() -> None:
        async with (
            app.router.lifespan_context(app),
            AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client,
        ):
            before = await client.get("/api/v1/health")
            assert before.status_code == 503
            assert before.json()["code"] == "db_not_ready"
            assert not app_path.exists()

            await asyncio.to_thread(command.upgrade, Config(str(ALEMBIC_INI)), "head")
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok", "database": "ready"}
            assert (await client.get("/health")).status_code == 404
            assert not demo_path.exists()

            await asyncio.to_thread(command.downgrade, Config(str(ALEMBIC_INI)), "base")
            assert (await client.get("/api/v1/health")).status_code == 503

    asyncio.run(check_readiness())


def test_database_connections_enforce_foreign_keys(tmp_path: Path) -> None:
    engine = open_engine(tmp_path / "app.sqlite", create=True)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
    finally:
        engine.dispose()


def test_same_database_paths_and_aliases_are_rejected(tmp_path: Path) -> None:
    regular = tmp_path / "app.sqlite"
    alias = tmp_path / "demo.sqlite"
    with pytest.raises(ValidationError, match="separate files"):
        Settings(app_db=regular, demo_db=regular)
    regular.touch()
    alias.symlink_to(regular)
    with pytest.raises(ValidationError, match="separate files"):
        Settings(app_db=regular, demo_db=alias)
