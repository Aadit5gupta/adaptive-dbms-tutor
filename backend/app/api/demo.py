"""Loopback-only browser API for dedicated synthetic learners."""

from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.schemas.assessment import AnswerInput, AnswerResult, SessionView, SQLAnswerInput
from app.services.assessment import AssessmentError, preview_sql, submit_mcq, submit_sql
from app.services.demo import (
    Activity,
    DemoState,
    Learner,
    LessonView,
    demo_state,
    recommended_lesson,
    require_learner,
    start_activity,
    visible_exercise,
)
from content.sql_results import ResultRows

LOOPBACK = {"127.0.0.1", "localhost", "::1"}
ORIGINS = frozenset(
    f"http://{host}:{port}" for host in ("localhost", "127.0.0.1", "[::1]") for port in (5173, 8000)
)


def loopback_only(request: Request) -> None:
    try:
        host = urlsplit("//" + request.headers.get("host", "")).hostname
    except ValueError:
        host = None
    if request.client is None or request.client.host not in LOOPBACK or host not in LOOPBACK:
        raise AssessmentError("The demo is available on loopback only.", "demo_loopback_only", 403)
    if request.method != "GET" and request.headers.get("origin") not in ORIGINS:
        raise AssessmentError("Open the demo on the local frontend.", "invalid_origin", 403)


class StartInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    activity: Activity


def demo_router(engine: Engine, root: Path) -> APIRouter:
    router = APIRouter(prefix="/demo", dependencies=[Depends(loopback_only)])

    @router.get("/{learner}", response_model=DemoState)
    def state(learner: Learner) -> DemoState:
        with Session(engine) as db:
            return demo_state(db, learner)

    @router.post("/{learner}/sessions", response_model=SessionView)
    def start(learner: Learner, body: StartInput) -> SessionView:
        with Session(engine) as db, db.begin():
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            return start_activity(db, learner, body.activity)

    @router.post("/{learner}/sessions/{session_id}/answer", response_model=AnswerResult)
    def answer(
        learner: Learner, session_id: str, body: AnswerInput, idempotency_key: str = Header()
    ) -> AnswerResult:
        with Session(engine) as db:
            user = require_learner(db, learner)
        return submit_mcq(engine, user, session_id, idempotency_key, body)

    @router.get("/{learner}/lesson", response_model=LessonView)
    def lesson(learner: Learner) -> LessonView:
        with Session(engine) as db:
            return recommended_lesson(db, learner)

    @router.post("/{learner}/sessions/{session_id}/sql/run", response_model=ResultRows)
    def sql_run(learner: Learner, session_id: str, body: SQLAnswerInput) -> ResultRows:
        with Session(engine) as db:
            exercise = visible_exercise(db, learner, session_id, body.item_id)
        return preview_sql(root, exercise, body.query)

    @router.post("/{learner}/sessions/{session_id}/sql/submit", response_model=AnswerResult)
    def sql_submit(
        learner: Learner,
        session_id: str,
        body: SQLAnswerInput,
        idempotency_key: str = Header(),
    ) -> AnswerResult:
        with Session(engine) as db:
            user = require_learner(db, learner)
        return submit_sql(engine, root, user, session_id, idempotency_key, body)

    return router
