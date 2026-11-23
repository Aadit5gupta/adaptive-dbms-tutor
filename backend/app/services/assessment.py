"""Server-owned allocation and deterministic MCQ submissions."""

from hashlib import sha256
from pathlib import Path
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
    SQLExerciseVersion,
)
from app.schemas.assessment import (
    AnswerInput,
    AnswerResult,
    ItemView,
    MasteryChange,
    SessionView,
    SQLAnswerInput,
)
from app.services.learning_state import mastery_for, recommend, save_recommendation
from app.services.misconceptions import update_misconception
from app.services.sql_grading import Grade, grade_sql
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


def allocate_sql(db: Session, user_id: str, logical_id: str) -> SessionView:
    version = db.scalar(
        select(QuestionVersion)
        .join(SQLExerciseVersion, SQLExerciseVersion.question_version_id == QuestionVersion.id)
        .where(QuestionVersion.question_id == logical_id, QuestionVersion.pool == "practice")
        .order_by(QuestionVersion.version.desc())
        .limit(1)
    )
    if version is None:
        raise AssessmentError("No reviewed SQL exercise is available.", "no_content", 404)
    session = AssessmentSession(
        id=uuid4().hex, user_id=user_id, kind="sql", status="open", created_at=int(time())
    )
    db.add(session)
    db.flush()
    db.add(
        SessionItem(
            id=uuid4().hex,
            session_id=session.id,
            question_version_id=version.id,
            position=0,
            status="open",
            revealing_hint_used=False,
        )
    )
    db.flush()
    return open_item_views(db, session)


def ensure_submission(
    db: Session, user_id: str, session_id: str, item_id: str
) -> tuple[AssessmentSession, SessionItem, QuestionVersion]:
    session = db.get(AssessmentSession, session_id)
    item = db.get(SessionItem, item_id)
    if (
        session is None
        or session.user_id != user_id
        or item is None
        or item.session_id != session.id
    ):
        raise AssessmentError("Assessment item not found.", "item_not_found", 404)
    if item.status != "open":
        raise AssessmentError("This assessment item already has a submission.", "already_answered")
    version = db.get(QuestionVersion, item.question_version_id)
    if version is None:
        raise AssessmentError("Question version unavailable.", "invalid_item")
    return session, item, version


def existing_submission(
    db: Session, user_id: str, key: str, fingerprint: str
) -> AnswerResult | None:
    committed = db.scalar(
        select(Attempt).where(Attempt.user_id == user_id, Attempt.idempotency_key == key)
    )
    if committed is None:
        return None
    if committed.request_fingerprint != fingerprint:
        raise AssessmentError("This submission key was already used.", "idempotency_conflict")
    return AnswerResult.model_validate_json(committed.result_json)


def fingerprint_for(session_id: str, key: str, answer: AnswerInput | SQLAnswerInput) -> str:
    if not key.isascii() or not 1 <= len(key) <= 128 or any(char.isspace() for char in key):
        raise AssessmentError("Supply a valid idempotency key.", "invalid_key", 422)
    return sha256(f"{session_id}:{answer.model_dump_json()}".encode()).hexdigest()


def persist_submission(
    engine: Engine,
    user_id: str,
    session_id: str,
    key: str,
    answer: AnswerInput | SQLAnswerInput,
    fingerprint: str,
    sql_grade: Grade | None = None,
    expected_version: str | None = None,
) -> AnswerResult:
    with Session(engine) as db, db.begin():
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        committed = existing_submission(db, user_id, key, fingerprint)
        if committed is not None:
            return committed
        session, item, version = ensure_submission(db, user_id, session_id, answer.item_id)
        question = db.get(Question, version.question_id)
        if question is None:
            raise AssessmentError("Question information unavailable.", "invalid_item")

        option: QuestionOption | None = None
        if isinstance(answer, AnswerInput):
            option = db.get(QuestionOption, (version.id, answer.option_index))
            if question.type != "mcq" or version.explanation is None or option is None:
                raise AssessmentError("This item cannot be graded as an MCQ.", "invalid_item")
            correct = option.is_correct
            explanation = version.explanation
            feedback_code = "correct" if correct else "incorrect"
        else:
            if sql_grade is None or question.type != "sql" or version.id != expected_version:
                raise AssessmentError("The SQL exercise version changed.", "invalid_item")
            correct = sql_grade.correct
            feedback_code = sql_grade.feedback_code
            explanation = SQL_FEEDBACK.get(
                feedback_code, "Review the query syntax and exercise schema."
            )

        attempt = Attempt(
            id=uuid4().hex,
            user_id=user_id,
            session_item_id=item.id,
            question_version_id=version.id,
            idempotency_key=key,
            request_fingerprint=fingerprint,
            selected_option_index=answer.option_index if isinstance(answer, AnswerInput) else None,
            submitted_sql=answer.query if isinstance(answer, SQLAnswerInput) else None,
            correct=correct,
            hint_used=item.revealing_hint_used,
            context=session.kind,
            created_at=int(time()),
        )
        with db.no_autoflush:
            before, after = mastery_for(db, attempt, question)
            hypothesis = (
                update_misconception(db, attempt, item, version, option)
                if option is not None
                else None
            )
            action, decision = recommend(db, attempt, question.subtopic_id, after, hypothesis)
        result = AnswerResult(
            attempt_id=attempt.id,
            correct=correct,
            explanation=explanation,
            feedback_code=feedback_code,
            mastery=MasteryChange(
                before=before.score, after=after.score, confidence=after.confidence
            ),
            next_action=action,
        )
        attempt.result_json = result.model_dump_json()
        db.add(attempt)
        db.flush()
        save_recommendation(db, attempt, decision, action)

        item.status = "answered"
        db.flush()
        remaining = db.scalar(
            select(SessionItem.id)
            .where(SessionItem.session_id == session.id, SessionItem.status == "open")
            .limit(1)
        )
        if remaining is None:
            session.status = "completed"
            session.completed_at = attempt.created_at
        return result


SQL_FEEDBACK = {
    "correct": "The query returned the required results on all grading fixtures.",
    "result_mismatch": "The result differs from the requested output. Check which rows and columns should appear.",
    "execution_limit": "The query exceeded the execution limit. Try reducing unnecessary row combinations.",
    "output_limit": "The result exceeded the size limit. Check the expected rows and columns.",
    "query_denied": "Use a SELECT query against the exercise tables.",
}


def submit_mcq(
    engine: Engine, user_id: str, session_id: str, key: str, answer: AnswerInput
) -> AnswerResult:
    return persist_submission(
        engine, user_id, session_id, key, answer, fingerprint_for(session_id, key, answer)
    )


def submit_sql(
    engine: Engine, root: Path, user_id: str, session_id: str, key: str, answer: SQLAnswerInput
) -> AnswerResult:
    fingerprint = fingerprint_for(session_id, key, answer)
    with Session(engine) as db:
        committed = existing_submission(db, user_id, key, fingerprint)
        if committed is not None:
            return committed
        _, _, version = ensure_submission(db, user_id, session_id, answer.item_id)
        exercise = db.get(SQLExerciseVersion, version.id)
        if exercise is None:
            raise AssessmentError("This item cannot be graded as SQL.", "invalid_item")
        version_id = version.id

    grade = grade_sql(root, exercise, answer.query)
    if grade.feedback_code == "worker_unavailable":
        raise AssessmentError("SQL grading is temporarily unavailable.", "worker_unavailable", 503)
    return persist_submission(
        engine, user_id, session_id, key, answer, fingerprint, grade, version_id
    )
