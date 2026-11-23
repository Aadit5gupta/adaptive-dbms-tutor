"""Local synthetic learner flow over the real assessment services."""

from typing import Literal

from pydantic import BaseModel
from sqlalchemy import case, delete, select
from sqlalchemy.orm import Session

from app.core.demo import DEMO_APPLICATION_ID, DEMO_LEARNERS, seed_demo_users
from app.db.models import (
    AssessmentSession,
    LessonVersion,
    Mastery,
    Misconception,
    Question,
    QuestionVersion,
    SessionItem,
    SQLExerciseVersion,
    User,
    UserMisconception,
)
from app.schemas.assessment import SessionView
from app.services.adaptive import NextAction
from app.services.assessment import AssessmentError, allocate_mcqs, allocate_sql, open_item_views
from app.services.progress import latest_recommendation
from app.services.sql_grading import worker_supported
from content.schemas.models import Misconception as Definition

Learner = Literal["a", "b"]
Activity = Literal["diagnostic", "practice", "checkpoint", "sql"]
DEMO_TOPICS = {"a": "relational.keys", "b": "sql.joins"}


class ProgressItem(BaseModel):
    topic: str
    score: float
    confidence: str
    attempts: int


class HypothesisView(BaseModel):
    code: str
    state: str
    evidence_count: int


class DemoState(BaseModel):
    learner: Learner
    topic: str
    activities: list[Activity]
    recommendation: NextAction | None
    progress: list[ProgressItem]
    hypotheses: list[HypothesisView]
    session: SessionView | None
    activity: Activity | None
    sql_ready: bool


class LessonView(BaseModel):
    title: str
    body: str
    source_url: str


def require_learner(db: Session, learner: Learner) -> str:
    user_id = DEMO_LEARNERS[learner]
    user = db.get(User, user_id)
    if user is None or not user.is_demo:
        raise AssessmentError("Run the demo seed script first.", "demo_not_seeded", 503)
    return user_id


def reset_learners(db: Session) -> None:
    if db.connection().exec_driver_sql("PRAGMA application_id").scalar_one() != DEMO_APPLICATION_ID:
        raise ValueError("reset requires the marked demo database")
    db.execute(delete(User).where(User.is_demo.is_(True), User.id.in_(DEMO_LEARNERS.values())))


def seed_learners(db: Session) -> None:
    seed_demo_users(db.connection())
    for learner in ("a", "b"):
        require_learner(db, learner)


def recent_session(db: Session, user_id: str) -> AssessmentSession | None:
    return db.scalar(
        select(AssessmentSession)
        .where(
            AssessmentSession.user_id == user_id,
            AssessmentSession.status == "open",
        )
        .order_by(AssessmentSession.created_at.desc(), AssessmentSession.id)
        .limit(1)
    )


def first_sql_exercise(db: Session) -> str | None:
    return db.scalar(
        select(QuestionVersion.question_id)
        .join(
            SQLExerciseVersion,
            SQLExerciseVersion.question_version_id == QuestionVersion.id,
        )
        .where(QuestionVersion.pool == "practice")
        .order_by(
            case((QuestionVersion.question_id == "sql_join_001", 0), else_=1),
            QuestionVersion.question_id,
        )
        .limit(1)
    )


def demo_state(db: Session, learner: Learner) -> DemoState:
    user_id = require_learner(db, learner)
    topic = DEMO_TOPICS[learner]
    available = set(
        db.scalars(
            select(QuestionVersion.pool)
            .join(Question, Question.id == QuestionVersion.question_id)
            .where(Question.subtopic_id == topic, Question.type == "mcq")
        )
    )
    activities: list[Activity] = []
    if "diagnostic" in available:
        activities.append("diagnostic")
    if "practice" in available:
        activities.append("practice")
    sql_ready = worker_supported() and first_sql_exercise(db) is not None
    if sql_ready:
        activities.append("sql")
    recommendation = latest_recommendation(db, user_id)
    if recommendation and recommendation.misconception_code:
        activities.append("checkpoint")
    active = recent_session(db, user_id)
    kind: Activity | None = None
    if active and active.kind in ("diagnostic", "practice", "checkpoint", "sql"):
        kinds: dict[str, Activity] = {
            "diagnostic": "diagnostic",
            "practice": "practice",
            "checkpoint": "checkpoint",
            "sql": "sql",
        }
        kind = kinds[active.kind]

    return DemoState(
        learner=learner,
        topic=topic,
        activities=activities,
        recommendation=recommendation,
        progress=[
            ProgressItem(
                topic=row.subtopic_id,
                score=row.score,
                confidence=row.confidence_level,
                attempts=row.attempts_count,
            )
            for row in db.scalars(
                select(Mastery).where(Mastery.user_id == user_id).order_by(Mastery.subtopic_id)
            )
        ],
        hypotheses=[
            HypothesisView(code=row.code, state=row.state, evidence_count=row.evidence_count)
            for row in db.scalars(
                select(UserMisconception)
                .where(UserMisconception.user_id == user_id)
                .order_by(UserMisconception.code)
            )
        ],
        session=open_item_views(db, active) if active else None,
        activity=kind,
        sql_ready=sql_ready,
    )


def start_activity(db: Session, learner: Learner, activity: Activity) -> SessionView:
    user_id = require_learner(db, learner)
    active = recent_session(db, user_id)
    if active is not None:
        if active.kind != activity:
            raise AssessmentError("Finish your current activity first.", "activity_open")
        return open_item_views(db, active)
    if activity == "sql":
        exercise = first_sql_exercise(db)
        if not worker_supported() or not exercise:
            raise AssessmentError("Reviewed SQL practice is unavailable.", "no_content", 404)
        return allocate_sql(db, user_id, exercise)
    if activity == "checkpoint":
        state = demo_state(db, learner)
        code = state.recommendation.misconception_code if state.recommendation else None
        definition = db.get(Misconception, code) if code else None
        if definition is None or not definition.enabled:
            raise AssessmentError("No checkpoint is currently recommended.", "no_checkpoint", 404)
        rule = Definition.model_validate_json(definition.definition_json)
        return allocate_mcqs(
            db,
            user_id,
            "checkpoint",
            limit=2,
            subtopic=rule.subtopic_id,
            misconception_code=rule.code,
            reserved_refs=rule.checkpoint_question_refs,
        )
    return allocate_mcqs(db, user_id, activity, subtopic=DEMO_TOPICS[learner])


def recommended_lesson(db: Session, learner: Learner) -> LessonView:
    state = demo_state(db, learner)
    ref = state.recommendation.lesson_ref if state.recommendation else None
    lesson = db.get(LessonVersion, ref) if ref else None
    if lesson is None:
        raise AssessmentError("No reviewed lesson is currently recommended.", "no_content", 404)
    from content.schemas.models import Source

    source = Source.model_validate_json(lesson.source_ref)
    return LessonView(
        title=lesson.title, body=lesson.body_markdown, source_url=str(source.factual_reference_url)
    )


def visible_exercise(
    db: Session, learner: Learner, session_id: str, item_id: str
) -> SQLExerciseVersion:
    user_id = require_learner(db, learner)
    row = db.execute(
        select(SQLExerciseVersion)
        .join(
            SessionItem,
            SessionItem.question_version_id == SQLExerciseVersion.question_version_id,
        )
        .join(AssessmentSession, AssessmentSession.id == SessionItem.session_id)
        .where(
            SessionItem.id == item_id,
            AssessmentSession.id == session_id,
            AssessmentSession.user_id == user_id,
        )
    ).scalar_one_or_none()
    if row is None:
        raise AssessmentError("SQL exercise not found.", "item_not_found", 404)
    return row
