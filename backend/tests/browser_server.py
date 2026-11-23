"""Local server for browser E2E, using isolated synthetic test data."""

from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from alembic import command
from alembic.config import Config
from app.api.demo import demo_router
from app.core.config import Settings
from app.core.db import open_engine
from app.core.demo import demo_path, ensure_demo_marker
from app.main import ALEMBIC_INI, create_app
from app.services.curriculum import publish_from_disk
from app.services.demo import seed_learners

from scripts.demo_support import demo_write

from .content_fixtures import make_foundation, make_s1_content


def run() -> None:
    with TemporaryDirectory(prefix="dbms-browser-test-") as directory:
        root = Path(directory)
        bank = make_s1_content(make_foundation(root / "bank"))
        settings = Settings(
            app_db=root / "app.sqlite", demo_db=root / "demo.sqlite", demo_enabled=False
        )
        app = create_app(settings)
        admin = open_engine(settings.app_db, create=True)
        engine = open_engine(demo_path(settings, settings.demo_db), create=True)
        try:
            for db in (admin, engine):
                cfg = Config(str(ALEMBIC_INI))
                with db.begin() as connection:
                    if db is engine:
                        ensure_demo_marker(connection)
                    cfg.attributes["connection"] = connection
                    command.upgrade(cfg, "head")
            with demo_write(engine) as session:
                publish_from_disk(session, bank)
                seed_learners(session)
            app.include_router(demo_router(engine, bank), prefix="/api/v1")
            uvicorn.run(app, host="127.0.0.1", port=8000, proxy_headers=False)
        finally:
            engine.dispose()
            admin.dispose()


if __name__ == "__main__":
    run()
