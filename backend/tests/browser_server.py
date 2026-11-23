"""Local server for browser E2E, using isolated synthetic test data."""

from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from alembic import command
from alembic.config import Config
from app.api.demo import demo_router
from app.api.tutor import local_tutor_router
from app.core.config import Settings
from app.core.db import open_engine
from app.core.demo import demo_path, ensure_demo_marker
from app.main import ALEMBIC_INI, create_app
from app.services.curriculum import publish_content
from app.services.demo import seed_learners
from app.services.retrieval import Retriever
from app.services.source_import import index_reviewed_lessons
from app.services.tutor import TutorService

from scripts.demo_support import demo_write
from scripts.validate_content import load_content

from .content_fixtures import make_foundation, make_s1_content


def run() -> None:
    with TemporaryDirectory(prefix="dbms-browser-test-") as directory:
        root = Path(directory)
        bank = make_s1_content(make_foundation(root / "bank"))
        settings = Settings(
            app_db=root / "app.sqlite",
            demo_db=root / "demo.sqlite",
            demo_enabled=False,
            tutor_provider="curated",
        )
        app = create_app(settings, content_root=bank)
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
            content = load_content(bank)
            for target in (admin, engine):
                with demo_write(target) as session:
                    publish_content(session, content, bank)
                    index_reviewed_lessons(session, content)
                    if target is engine:
                        seed_learners(session)
            app.include_router(demo_router(engine, bank), prefix="/api/v1")
            app.include_router(
                local_tutor_router(TutorService(Retriever(engine, bank)), engine), prefix="/api/v1"
            )
            uvicorn.run(app, host="127.0.0.1", port=8000, proxy_headers=False)
        finally:
            engine.dispose()
            admin.dispose()


if __name__ == "__main__":
    run()
