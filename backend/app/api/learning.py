"""Signed-in curriculum, practice, progress and SQL lab."""

from pathlib import Path
from time import time
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import Accounts
from app.db.models import (
    AssessmentSession,
    Misconception,
    QuestionVersion,
    SessionItem,
    SQLExerciseVersion,
    UserMisconception,
)
from app.schemas.assessment import AnswerInput, AnswerResult, SessionView, SQLAnswerInput
from app.schemas.tutor import Topic
from app.services.adaptive import NextAction
from app.services.assessment import (
    AssessmentError,
    allocate_sql,
    open_item_views,
    submit_mcq,
    submit_sql,
)
from app.services.catalog import (
    DomainView,
    ExerciseView,
    LessonDetail,
    course,
    lesson_detail,
    reviewed_exercises,
)
from app.services.progress import Progress, latest_recommendation, read_progress
from app.services.sql_grading import WorkerError, run_visible, worker_supported
from app.services.study import start_checkpoints, start_study, study_session
from content.sql_results import ResultRows


class PracticeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    mode: Literal["practice", "review"] = "practice"


class DiagnosticInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic | None = None


class SqlInput(SQLAnswerInput):
    session_id: Annotated[str, Field(min_length=1, max_length=64)]


class Hypothesis(BaseModel):
    code: str
    title: str
    topic_id: str
    state: str
    evidence_count: int


def first_question(view: SessionView) -> SessionView:
    return view.model_copy(update={"items": view.items[:1]})


def learning_router(accounts: Accounts, root: Path) -> APIRouter:
    router = APIRouter(dependencies=[Depends(accounts.require_user)])
    engine = accounts.engine
    identity = accounts.require_user

    @router.get("/curriculum")
    def curriculum() -> list[DomainView]:
        with Session(engine) as db:
            return course(db, root)

    @router.get("/lessons/{ref}")
    def lesson(ref: str) -> LessonDetail:
        with Session(engine) as db:
            return lesson_detail(db, ref)

    @router.post("/practice/sessions")
    def practice(body: PracticeInput, user_id: Annotated[str, Depends(identity)]) -> SessionView:
        with Session(engine) as db, db.begin():
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            return first_question(
                start_study(db, user_id, body.mode, topic=body.topic, difficulty=body.difficulty)
            )

    @router.post("/assessments/start")
    def diagnostic(
        body: DiagnosticInput, user_id: Annotated[str, Depends(identity)]
    ) -> SessionView:
        with Session(engine) as db, db.begin():
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            return first_question(start_study(db, user_id, "diagnostic", topic=body.topic))

    @router.post("/practice/checkpoints")
    def checkpoints(user_id: Annotated[str, Depends(identity)]) -> SessionView:
        with Session(engine) as db, db.begin():
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            return first_question(start_checkpoints(db, user_id))

    @router.get("/practice/sessions/{sid}")
    def current(sid: str, user_id: Annotated[str, Depends(identity)]) -> SessionView:
        with Session(engine) as db:
            return first_question(study_session(db, user_id, sid))

    @router.post("/practice/sessions/{sid}/answer")
    @router.post("/assessments/{sid}/submit")
    def answer(
        sid: str,
        body: AnswerInput,
        user_id: Annotated[str, Depends(identity)],
        idempotency_key: str = Header(),
    ) -> AnswerResult:
        return submit_mcq(engine, user_id, sid, idempotency_key, body)

    @router.get("/recommendations/next")
    def recommendation(user_id: Annotated[str, Depends(identity)]) -> NextAction | None:
        with Session(engine) as db:
            return latest_recommendation(db, user_id)

    @router.get("/progress")
    def progress(user_id: Annotated[str, Depends(identity)]) -> Progress:
        with Session(engine) as db:
            return read_progress(db, user_id, int(time()))

    @router.get("/misconceptions")
    def hypotheses(user_id: Annotated[str, Depends(identity)]) -> list[Hypothesis]:
        with Session(engine) as db:
            return [
                Hypothesis(
                    code=row.code,
                    title=rule.title,
                    topic_id=rule.subtopic_id,
                    state=row.state,
                    evidence_count=row.evidence_count,
                )
                for row, rule in db.execute(
                    select(UserMisconception, Misconception)
                    .join(Misconception, Misconception.code == UserMisconception.code)
                    .where(UserMisconception.user_id == user_id, Misconception.enabled.is_(True))
                    .order_by(UserMisconception.code)
                )
            ]

    @router.get("/sql/exercises")
    def exercises() -> list[ExerciseView]:
        with Session(engine) as db:
            return reviewed_exercises(db)

    @router.get("/sql/exercises/{logical_id}")
    def exercise(logical_id: str) -> ExerciseView:
        with Session(engine) as db:
            item = next((row for row in reviewed_exercises(db) if row.id == logical_id), None)
        if item is None:
            raise AssessmentError("The SQL exercise is unavailable.", "no_content", 404)
        return item

    @router.post("/sql/exercises/{logical_id}/sessions")
    def begin_sql(logical_id: str, user_id: Annotated[str, Depends(identity)]) -> SessionView:
        if not worker_supported():
            raise AssessmentError(
                "SQL execution is unavailable on this platform.", "worker_unavailable", 503
            )
        with Session(engine) as db, db.begin():
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            existing = db.scalar(
                select(AssessmentSession)
                .join(
                    SessionItem,
                    SessionItem.session_id == AssessmentSession.id,
                )
                .join(QuestionVersion, QuestionVersion.id == SessionItem.question_version_id)
                .where(
                    AssessmentSession.kind == "sql",
                    AssessmentSession.status == "open",
                    AssessmentSession.user_id == user_id,
                    QuestionVersion.question_id == logical_id,
                )
                .limit(1)
            )
            return (
                open_item_views(db, existing) if existing else allocate_sql(db, user_id, logical_id)
            )

    def own_sql(user_id: str, logical_id: str, body: SqlInput) -> SQLExerciseVersion:
        with Session(engine) as db:
            exercise = db.scalar(
                select(SQLExerciseVersion)
                .join(QuestionVersion, QuestionVersion.id == SQLExerciseVersion.question_version_id)
                .join(SessionItem, SessionItem.question_version_id == QuestionVersion.id)
                .join(AssessmentSession, AssessmentSession.id == SessionItem.session_id)
                .where(
                    AssessmentSession.user_id == user_id,
                    AssessmentSession.id == body.session_id,
                    SessionItem.id == body.item_id,
                    QuestionVersion.question_id == logical_id,
                )
            )
        if exercise is None:
            raise AssessmentError("SQL exercise assignment not found.", "item_not_found", 404)
        return exercise

    @router.post("/sql/exercises/{logical_id}/run")
    def run_sql(
        logical_id: str, body: SqlInput, user_id: Annotated[str, Depends(identity)]
    ) -> ResultRows:
        result = run_visible(root, own_sql(user_id, logical_id, body), body.query)
        if isinstance(result, WorkerError):
            unavailable = result.error == "worker_unavailable"
            raise AssessmentError(
                "SQL preview is unavailable." if unavailable else "Check the query and try again.",
                result.error,
                503 if unavailable else 422,
            )
        return result

    @router.post("/sql/exercises/{logical_id}/submit")
    def answer_sql(
        logical_id: str,
        body: SqlInput,
        user_id: Annotated[str, Depends(identity)],
        idempotency_key: str = Header(),
    ) -> AnswerResult:
        own_sql(user_id, logical_id, body)
        return submit_sql(
            engine,
            root,
            user_id,
            body.session_id,
            idempotency_key,
            SQLAnswerInput(item_id=body.item_id, query=body.query),
        )

    return router
