import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.auth import COOKIE, LoginThrottle, token_hash
from app.core.config import Settings
from app.core.db import open_engine
from app.db.models import AuthSession, User
from app.main import ALEMBIC_INI, create_app
from app.services.assessment import AssessmentError
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

BASE_URL = "http://127.0.0.1:8000"
ORIGIN = {"Origin": BASE_URL}
PASSWORD = "synthetic account passphrase"
FIRST = {"email": "first@example.com", "password": PASSWORD}
SECOND = {"email": "second@example.com", "password": PASSWORD}


@pytest.fixture
def local_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[FastAPI, Settings]:
    monkeypatch.setenv("DBMS_APP_DB", str(tmp_path / "app.sqlite"))
    monkeypatch.setenv("DBMS_DEMO_DB", str(tmp_path / "demo.sqlite"))
    monkeypatch.setenv("DBMS_DEMO_ENABLED", "false")
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    settings = Settings()
    return create_app(settings), settings


def test_origin_protection_and_validation_error_redaction(
    local_app: tuple[FastAPI, Settings],
) -> None:
    app, _ = local_app

    async def run() -> None:
        async with AsyncClient(transport=ASGITransport(app), base_url=BASE_URL) as client:
            for headers in (
                {},
                {"Origin": "null"},
                {"Origin": "https://example.com", "Referer": BASE_URL},
                {"Referer": "http://127.0.0.1:8000.attacker.example/"},
                {"Referer": "http://127.0.0.1:8000@attacker.example/"},
            ):
                response = await client.post("/api/v1/auth/register", headers=headers, json=FIRST)
                assert response.status_code == 403
            invalid = await client.post(
                "/api/v1/auth/register",
                headers=ORIGIN,
                json={
                    "email": "not an email",
                    "password": "secret",
                },
            )
            assert invalid.status_code == 422 and "secret" not in invalid.text
            registered = await client.post(
                "/api/v1/auth/register", headers={"Referer": BASE_URL + "/register"}, json=FIRST
            )
            assert registered.status_code == 201

    asyncio.run(run())


def test_account_export_delete_and_logout_are_isolated(local_app: tuple[FastAPI, Settings]) -> None:
    app, settings = local_app
    engine = open_engine(settings.app_db)

    async def run() -> None:
        async with (
            app.router.lifespan_context(app),
            AsyncClient(transport=ASGITransport(app), base_url=BASE_URL, headers=ORIGIN) as a,
            AsyncClient(transport=ASGITransport(app), base_url=BASE_URL, headers=ORIGIN) as b,
        ):
            assert (await a.get("/api/v1/me")).status_code == 401
            first = await a.post("/api/v1/auth/register", json=FIRST)
            second = await b.post("/api/v1/auth/register", json=SECOND)
            assert first.status_code == second.status_code == 201
            token = a.cookies[COOKIE]
            assert (
                "HttpOnly" in first.headers["set-cookie"]
                and "SameSite=lax" in first.headers["set-cookie"]
            )
            with Session(engine) as db:
                row = db.scalar(
                    select(AuthSession).where(AuthSession.token_hash == token_hash(token))
                )
                assert row is not None and row.token_hash != token
                user = db.get(User, row.user_id)
                assert (
                    user is not None
                    and user.password_hash
                    and user.password_hash.startswith("$argon2id$")
                )

            settings_update = await a.patch(
                "/api/v1/me", json={"goal": "exam", "daily_minutes": 15}
            )
            assert settings_update.json()["preferences"]["goal"] == "exam"
            assert (await b.get("/api/v1/me")).json()["preferences"]["goal"] is None

            export = await a.get("/api/v1/me/export")
            assert export.status_code == 200
            assert export.headers["cache-control"] == "no-store"
            assert export.json()["profile"]["email"] == FIRST["email"]
            assert SECOND["email"] not in export.text and token not in export.text
            assert "password_hash" not in export.text and "token_hash" not in export.text

            assert (await a.post("/api/v1/auth/logout")).status_code == 200
            assert (
                await a.get("/api/v1/me", headers={"Cookie": f"{COOKIE}={token}"})
            ).status_code == 401
            assert (await a.post("/api/v1/auth/login", json=FIRST)).status_code == 200
            assert (await a.delete("/api/v1/me")).status_code == 200
            assert (await a.get("/api/v1/me/export")).status_code == 401
            assert (await a.post("/api/v1/auth/login", json=FIRST)).status_code == 401
            assert (await b.get("/api/v1/me")).json()["email"] == SECOND["email"]
            with Session(engine) as db:
                assert list(db.scalars(select(User.email))) == [SECOND["email"]]
                assert len(list(db.scalars(select(AuthSession)))) == 1

    try:
        asyncio.run(run())
    finally:
        engine.dispose()


def test_expired_cookie_is_unusable(local_app: tuple[FastAPI, Settings]) -> None:
    app, settings = local_app
    engine = open_engine(settings.app_db)

    async def run() -> None:
        async with AsyncClient(
            transport=ASGITransport(app), base_url=BASE_URL, headers=ORIGIN
        ) as client:
            assert (await client.post("/api/v1/auth/register", json=FIRST)).status_code == 201
            with Session(engine) as db, db.begin():
                db.execute(update(AuthSession).values(expires_at=0))
            assert (await client.get("/api/v1/me")).status_code == 401

    try:
        asyncio.run(run())
    finally:
        engine.dispose()


def test_login_throttle_bounds_attempts() -> None:
    throttle = LoginThrottle(maximum=2)
    throttle.check()
    throttle.check()
    with pytest.raises(AssessmentError) as error:
        throttle.check()
    assert error.value.status == 429


def test_signed_in_assessment_and_progress_are_private(
    local_app: tuple[FastAPI, Settings], s1: Path
) -> None:
    from app.db.models import Attempt
    from app.services.curriculum import publish_from_disk

    _, settings = local_app
    app = create_app(settings, content_root=s1)
    engine = open_engine(settings.app_db)
    with Session(engine) as db, db.begin():
        publish_from_disk(db, s1)

    async def run() -> None:
        async with (
            app.router.lifespan_context(app),
            AsyncClient(transport=ASGITransport(app), base_url=BASE_URL, headers=ORIGIN) as a,
            AsyncClient(transport=ASGITransport(app), base_url=BASE_URL, headers=ORIGIN) as b,
        ):
            assert (await a.get("/api/v1/curriculum")).status_code == 401
            assert (await a.post("/api/v1/auth/register", json=FIRST)).status_code == 201
            assert (await b.post("/api/v1/auth/register", json=SECOND)).status_code == 201
            curriculum = (await a.get("/api/v1/curriculum")).json()
            assert len(curriculum) == 7
            diag = await a.post("/api/v1/assessments/start", json={"topic": "relational.keys"})
            session = diag.json()
            assert diag.status_code == 200 and len(session["items"]) == 1
            sid, item = session["session_id"], session["items"][0]
            assert (await b.get(f"/api/v1/practice/sessions/{sid}")).status_code == 404
            assert "explanation" not in item and "is_correct" not in item
            body = {"item_id": item["item_id"], "option_index": 1}
            headers = {**ORIGIN, "Idempotency-Key": item["item_id"]}
            submitted = await a.post(
                f"/api/v1/assessments/{sid}/submit", json=body, headers=headers
            )
            assert submitted.status_code == 200 and not submitted.json()["correct"]
            assert (
                await a.post(f"/api/v1/assessments/{sid}/submit", json=body, headers=headers)
            ).json() == submitted.json()

            practice = await a.post("/api/v1/practice/sessions", json={"topic": "relational.keys"})
            allocation = practice.json()
            kind = allocation["items"][0]
            result = await a.post(
                f"/api/v1/practice/sessions/{allocation['session_id']}/answer",
                json={"item_id": kind["item_id"], "option_index": 1},
                headers={**ORIGIN, "Idempotency-Key": kind["item_id"]},
            )
            assert result.json()["next_action"]["action_type"] == "MISCONCEPTION_REMEDIATION"
            assert (await a.get("/api/v1/lessons/keys@1")).json()["title"] == "keys"
            checks = await a.post("/api/v1/practice/checkpoints")
            assert checks.json()["total"] == 2
            assert (await a.get("/api/v1/misconceptions")).json()[0]["state"] == "active"
            assert (await b.get("/api/v1/misconceptions")).json() == []
            assert len((await a.get("/api/v1/progress")).json()["recent"]) == 2
            assert (await b.get("/api/v1/progress")).json()["recent"] == []
            assert len((await a.get("/api/v1/me/export")).json()["attempts"]) == 2
            assert (await b.get("/api/v1/me/export")).json()["attempts"] == []
            assert (await a.delete("/api/v1/me")).status_code == 200
            with Session(engine) as db:
                assert list(db.scalars(select(Attempt))) == []
            assert (await b.get("/api/v1/me")).status_code == 200

    try:
        asyncio.run(run())
    finally:
        engine.dispose()
