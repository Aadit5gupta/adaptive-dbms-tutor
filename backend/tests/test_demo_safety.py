import asyncio
import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.core.db import open_engine
from app.core.demo import DEMO_LEARNERS, demo_path, ensure_demo_marker
from app.db.models import User
from app.main import ALEMBIC_INI
from app.services.curriculum import publish_from_disk
from app.services.demo import reset_learners, seed_learners
from app.services.sql_grading import worker_supported
from sqlalchemy.orm import Session

from scripts.demo_support import demo_write
from scripts.verify_demo import replay


def test_reset_preserves_regular_db_and_non_demo_rows(tmp_path: Path) -> None:
    settings = Settings(app_db=tmp_path / "app.sqlite", demo_db=tmp_path / "demo.sqlite")
    with closing(sqlite3.connect(settings.app_db)) as regular:
        regular.execute("CREATE TABLE sentinel(i INTEGER)")
        regular.commit()
    before = sha256(settings.app_db.read_bytes()).digest()
    cfg = Config(str(ALEMBIC_INI))
    engine = open_engine(demo_path(settings, settings.demo_db), create=True)
    try:
        with engine.begin() as connection:
            ensure_demo_marker(connection)
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        with demo_write(engine) as db:
            seed_learners(db)
            db.add(User(id="regular-user", is_demo=False, created_at=1))
        with demo_write(engine) as db:
            reset_learners(db)
        with Session(engine) as db:
            assert db.get(User, "regular-user") is not None
            for user in DEMO_LEARNERS.values():
                assert db.get(User, user) is None
    finally:
        engine.dispose()
    assert sha256(settings.app_db.read_bytes()).digest() == before


def test_demo_guard_rejects_an_existing_unmarked_file(tmp_path: Path) -> None:
    settings = Settings(app_db=tmp_path / "app.sqlite", demo_db=tmp_path / "demo.sqlite")
    with closing(sqlite3.connect(settings.demo_db)) as regular:
        regular.execute("CREATE TABLE sentinel(i INTEGER)")
    with pytest.raises(ValueError, match="missing the demo marker"):
        demo_path(settings, settings.demo_db)


@pytest.mark.skipif(not worker_supported(), reason="SQL worker is disabled on this platform")
def test_demo_replay_with_synthetic_verified_fixture(s1: Path) -> None:
    demo = s1 / "demo.sqlite"
    cfg = Config(str(ALEMBIC_INI))
    engine = open_engine(demo, create=True)
    try:
        with engine.begin() as connection:
            ensure_demo_marker(connection)
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        with demo_write(engine) as db:
            publish_from_disk(db, s1)
    finally:
        engine.dispose()
    replay(demo, s1)


def test_browser_reset_reseeds_both_learners_and_rejects_stale_work(s1: Path) -> None:
    from app.api.demo import demo_router
    from app.db.models import TutorConversation
    from app.main import create_app
    from app.schemas.tutor import TutorInput, TutorReply
    from app.services.assessment import AssessmentError
    from app.services.conversations import learner_snapshot, store_reply
    from httpx import ASGITransport, AsyncClient

    settings = Settings(app_db=s1 / "app.sqlite", demo_db=s1 / "demo.sqlite", demo_enabled=False)
    engine = open_engine(demo_path(settings, settings.demo_db), create=True)
    cfg = Config(str(ALEMBIC_INI))
    origin = {"Origin": "http://127.0.0.1:5173"}
    try:
        with engine.begin() as connection:
            ensure_demo_marker(connection)
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        with demo_write(engine) as db:
            publish_from_disk(db, s1)
            seed_learners(db)
            db.add(User(id="regular-user", is_demo=False, created_at=1))

        app = create_app(settings, content_root=s1)
        app.include_router(demo_router(engine, s1), prefix="/api/v1")

        async def run() -> None:
            reset = "/api/v1/demo/reset"
            remote = ASGITransport(app, client=("192.0.2.1", 12345))
            async with AsyncClient(transport=remote, base_url="http://127.0.0.1:8000") as client:
                assert (await client.post(reset, headers=origin)).status_code == 403

            transport = ASGITransport(app, client=("127.0.0.1", 12345))
            async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
                active = {}
                for learner in DEMO_LEARNERS:
                    response = await client.post(
                        f"/api/v1/demo/{learner}/sessions",
                        json={"activity": "diagnostic"},
                        headers=origin,
                    )
                    assert response.status_code == 200
                    active[learner] = response.json()
                old_a = active["a"]
                answer_a = {
                    "item_id": old_a["items"][0]["item_id"],
                    "option_index": 1,
                }
                route_a = f"/api/v1/demo/a/sessions/{old_a['session_id']}/answer"
                assert (
                    await client.post(
                        route_a,
                        json=answer_a,
                        headers={**origin, "Idempotency-Key": "first-answer"},
                    )
                ).status_code == 200

                user = DEMO_LEARNERS["a"]
                reply = TutorReply(
                    answer="Synthetic reply",
                    mode="ask",
                    provider="curated",
                    degraded=False,
                    status="ok",
                    citations=[],
                )
                question = TutorInput(query="Explain keys", topic_id="relational.keys")
                existing = learner_snapshot(engine, user, question, demo=True)
                store_reply(engine, user, existing, reply)
                pending = learner_snapshot(engine, user, question, demo=True)

                assert (await client.post(reset)).status_code == 403
                assert (
                    await client.post(reset, headers={"Origin": "https://example.invalid"})
                ).status_code == 403
                assert (await client.get("/api/v1/demo/a")).json()["progress"]
                assert (await client.post(reset, headers=origin)).json() == {"ok": True}
                assert (await client.post(reset, headers=origin)).json() == {"ok": True}

                for learner in DEMO_LEARNERS:
                    state = (await client.get(f"/api/v1/demo/{learner}")).json()
                    assert state["progress"] == state["hypotheses"] == []
                    assert state["recommendation"] is state["session"] is None
                    assert "diagnostic" in state["activities"]

                assert (
                    await client.post(
                        route_a,
                        json=answer_a,
                        headers={**origin, "Idempotency-Key": "first-answer"},
                    )
                ).status_code == 404
                with pytest.raises(AssessmentError, match="Tutor conversation not found"):
                    store_reply(engine, user, pending, reply)
                with Session(engine) as db:
                    assert db.get(User, "regular-user") is not None
                    assert db.get(TutorConversation, existing.id) is None

        asyncio.run(run())
    finally:
        engine.dispose()
