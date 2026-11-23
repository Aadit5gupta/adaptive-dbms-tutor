"""Server-owned allocation and deterministic MCQ submissions."""

from hashlib import sha256
from time import time
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import (
    AssessmentSession,
    Attempt,
    Question,
    QuestionOption,
    QuestionVersion,
    SessionItem,
)
from app.schemas.assessment import AnswerInput, AnswerResult, ItemView, SessionView
from content.schemas.models import Pool


class AssessmentError(ValueError):
    def __init__(self, detail: str, code: str, status: int = 409):
        super().__init__(detail)
        self.code = code
        self.status = status


def options_for(db: Session, question_ref: str) -> list[QuestionOption]:
    return list(
        db.scalars(
            select(QuestionOption)
            .where(QuestionOption.question_version_id == question_ref)
            .order_by(QuestionOption.option_index)
        )
    )


def open_item_views(db: Session, session: AssessmentSession) -> SessionView:
    items = db.execute(
        select(SessionItem, QuestionVersion, Question)
        .join(QuestionVersion, SessionItem.question_version_id == QuestionVersion.id)
        .join(Question, Question.id == QuestionVersion.question_id)
        .where(SessionItem.session_id == session.id, SessionItem.status == "open")
        .order_by(SessionItem.position)
    )
    return SessionView(
        session_id=session.id,
        items=[
            ItemView(
                item_id=item.id,
                question_ref=version.id,
                subtopic_id=question.subtopic_id,
                stem=version.stem,
                options=[option.body for option in options_for(db, version.id)],
            )
            for item, version, question in items
        ],
    )


def allocate_mcqs(
    db: Session,
    user_id: str,
    pool: Pool,
    *,
    limit: int = 1,
    subtopic: str | None = None,
    reserved_refs: tuple[str, ...] = (),
    misconception_code: str | None = None,
) -> SessionView:
    if pool not in ("practice", "diagnostic", "checkpoint"):
        raise AssessmentError("This pool is reserved.", "reserved_pool")
    if pool == "checkpoint" and (not reserved_refs or not misconception_code):
        raise AssessmentError("No verified checkpoint is available.", "no_content", 404)

    latest = (
        select(QuestionVersion.question_id, func.max(QuestionVersion.version).label("version"))
        .group_by(QuestionVersion.question_id)
        .subquery()
    )
    query = (
        select(QuestionVersion)
        .join(Question, Question.id == QuestionVersion.question_id)
        .where(Question.type == "mcq", QuestionVersion.pool == pool)
    )
    if subtopic is not None:
        query = query.where(Question.subtopic_id == subtopic)
    if pool == "checkpoint":
        seen = (
            select(QuestionVersion.question_id)
            .join(SessionItem, SessionItem.question_version_id == QuestionVersion.id)
            .join(AssessmentSession, AssessmentSession.id == SessionItem.session_id)
            .where(AssessmentSession.user_id == user_id)
        )
        query = query.where(QuestionVersion.id.in_(reserved_refs), Question.id.not_in(seen))
    else:
        query = query.join(
            latest,
            (QuestionVersion.question_id == latest.c.question_id)
            & (QuestionVersion.version == latest.c.version),
        )
    versions = list(db.scalars(query.order_by(Question.id).limit(limit)))
    if not versions:
        raise AssessmentError(
            "There are no eligible questions for this activity.", "no_content", 404
        )

    session = AssessmentSession(
        id=uuid4().hex, user_id=user_id, kind=pool, status="open", created_at=int(time())
    )
    db.add(session)
    db.flush()
    db.add_all(
        SessionItem(
            id=uuid4().hex,
            session_id=session.id,
            question_version_id=version.id,
            position=index,
            status="open",
            revealing_hint_used=False,
            remediation_code=misconception_code,
        )
        for index, version in enumerate(versions)
    )
    db.flush()
    return open_item_views(db, session)


def submit_mcq(
    engine: Engine, user_id: str, session_id: str, key: str, answer: AnswerInput
) -> AnswerResult:
    fingerprint = sha256(f"{session_id}:{answer.model_dump_json()}".encode()).hexdigest()
    with Session(engine) as db, db.begin():
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        committed = db.scalar(
            select(Attempt).where(Attempt.user_id == user_id, Attempt.idempotency_key == key)
        )
        if committed is not None:
            if committed.request_fingerprint != fingerprint:
                raise AssessmentError(
                    "This submission key was already used.", "idempotency_conflict"
                )
            return AnswerResult.model_validate_json(committed.result_json)

        session = db.get(AssessmentSession, session_id)
        item = db.get(SessionItem, answer.item_id)
        if (
            session is None
            or session.user_id != user_id
            or item is None
            or item.session_id != session.id
        ):
            raise AssessmentError("Assessment item not found.", "item_not_found", 404)
        if item.status != "open":
            raise AssessmentError(
                "This assessment item already has a submission.", "already_answered"
            )
        version = db.get(QuestionVersion, item.question_version_id)
        option = db.get(QuestionOption, (item.question_version_id, answer.option_index))
        if version is None or version.explanation is None or option is None:
            raise AssessmentError(
                "This assessment item cannot be graded as an MCQ.", "invalid_item"
            )

        now = int(time())
        result = AnswerResult(
            attempt_id=uuid4().hex, correct=option.is_correct, explanation=version.explanation
        )
        db.add(
            Attempt(
                id=result.attempt_id,
                user_id=user_id,
                session_item_id=item.id,
                question_version_id=version.id,
                idempotency_key=key,
                request_fingerprint=fingerprint,
                result_json=result.model_dump_json(),
                selected_option_index=answer.option_index,
                correct=result.correct,
                hint_used=item.revealing_hint_used,
                context=session.kind,
                created_at=now,
            )
        )
        item.status = "answered"
        db.flush()
        remaining = db.scalar(
            select(SessionItem.id)
            .where(SessionItem.session_id == session.id, SessionItem.status == "open")
            .limit(1)
        )
        if remaining is None:
            session.status = "completed"
            session.completed_at = now
        return result
