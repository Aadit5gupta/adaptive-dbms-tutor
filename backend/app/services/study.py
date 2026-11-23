"""Resume or allocate review, practice, and diagnostic sessions."""

from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AssessmentSession, Question, QuestionVersion, SessionItem
from app.schemas.assessment import SessionView
from app.services.assessment import AssessmentError, allocate_mcqs, open_item_views

StudyMode = Literal["practice", "diagnostic", "review"]


def study_session(db: Session, user_id: str, session_id: str) -> SessionView:
    owned = db.get(AssessmentSession, session_id)
    if owned is None or owned.user_id != user_id:
        raise AssessmentError("Assessment session not found.", "session_not_found", 404)
    return open_item_views(db, owned)


def start_study(
    db: Session,
    user_id: str,
    mode: StudyMode,
    *,
    topic: str | None = None,
    difficulty: str | None = None,
) -> SessionView:
    """Caller holds a short immediate transaction during allocation and resumption."""
    query = select(AssessmentSession).where(
        AssessmentSession.user_id == user_id,
        AssessmentSession.kind == mode,
        AssessmentSession.status == "open",
    )
    if topic:
        eligible = (
            select(SessionItem.session_id)
            .join(QuestionVersion, QuestionVersion.id == SessionItem.question_version_id)
            .join(Question, Question.id == QuestionVersion.question_id)
            .where(Question.subtopic_id == topic)
        )
        query = query.where(AssessmentSession.id.in_(eligible))
    existing = db.scalar(
        query.order_by(AssessmentSession.created_at.desc(), AssessmentSession.id).limit(1)
    )
    if existing is not None:
        return open_item_views(db, existing)
    if mode == "diagnostic":
        return allocate_mcqs(
            db,
            user_id,
            "diagnostic",
            subtopic=topic,
            limit=3 if topic else 21,
            fresh_only=True,
            balance_domains=topic is None,
        )
    return allocate_mcqs(
        db,
        user_id,
        "practice",
        subtopic=topic,
        limit=5,
        prefer_difficulty=difficulty,
        context=mode,
    )


def start_checkpoints(db: Session, user_id: str) -> SessionView:
    from app.db.models import Misconception, UserMisconception
    from app.services.progress import latest_recommendation
    from content.schemas.models import Misconception as Definition

    action = latest_recommendation(db, user_id)
    code = action.misconception_code if action else None
    rule = db.get(Misconception, code) if code else None
    state = db.get(UserMisconception, (user_id, code)) if code else None
    if (
        rule is None
        or not rule.enabled
        or state is None
        or state.state not in ("active", "improving")
    ):
        raise AssessmentError("No checkpoint is currently recommended.", "no_checkpoint", 404)
    existing = db.scalar(
        select(AssessmentSession)
        .join(SessionItem, SessionItem.session_id == AssessmentSession.id)
        .where(
            AssessmentSession.user_id == user_id,
            AssessmentSession.status == "open",
            AssessmentSession.kind == "checkpoint",
            SessionItem.remediation_code == rule.code,
        )
        .limit(1)
    )
    if existing:
        return open_item_views(db, existing)
    definition = Definition.model_validate_json(rule.definition_json)
    return allocate_mcqs(
        db,
        user_id,
        "checkpoint",
        limit=2,
        subtopic=rule.subtopic_id,
        reserved_refs=definition.checkpoint_question_refs,
        misconception_code=rule.code,
    )
