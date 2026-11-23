"""Transactional learner state transitions shared by MCQ and SQL grading."""

import json
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AssessmentSession,
    Attempt,
    Lesson,
    LessonVersion,
    Mastery,
    MasteryHistory,
    Misconception,
    PolicyDecision,
    Question,
    QuestionVersion,
    Recommendation,
    SessionItem,
    TopicPrerequisite,
    UserMisconception,
)
from app.services.adaptive import NextAction, PolicyInput, Remediation, choose_next
from app.services.mastery import (
    MODEL_NAME,
    MODEL_VERSION,
    AttemptEvidence,
    MasteryState,
    update_mastery,
)
from app.services.sql_grading import worker_supported
from content.schemas.models import Misconception as Definition


def independent_answer(db: Session, attempt: Attempt, logical_id: str) -> bool:
    if attempt.hint_used:
        return False
    earlier = db.scalar(
        select(Attempt.id)
        .join(QuestionVersion, QuestionVersion.id == Attempt.question_version_id)
        .where(
            Attempt.user_id == attempt.user_id,
            QuestionVersion.question_id == logical_id,
            Attempt.hint_used.is_(False),
            Attempt.context.not_in(("pre_test_a", "post_test_b")),
        )
        .limit(1)
    )
    return earlier is None


def mastery_for(
    db: Session, attempt: Attempt, question: Question
) -> tuple[MasteryState, MasteryState]:
    key = (attempt.user_id, question.subtopic_id, MODEL_NAME)
    row = db.get(Mastery, key)
    before = (
        MasteryState()
        if row is None
        else MasteryState(
            score=row.score,
            attempts=row.attempts_count,
            distinct=row.distinct_question_count,
            review_due_at=row.review_due_at,
            review_step=row.review_interval_step,
        )
    )
    after = update_mastery(
        before,
        AttemptEvidence(
            correct=attempt.correct,
            first_independent_answer=independent_answer(db, attempt, question.id),
            recorded_at=attempt.created_at,
            review=attempt.context == "review",
            held_out=attempt.context in ("pre_test_a", "post_test_b"),
        ),
    )
    if after is before:
        return before, after
    if row is None:
        row = Mastery(user_id=key[0], subtopic_id=key[1], model_name=key[2])
        db.add(row)
    row.score = after.score
    row.attempts_count = after.attempts
    row.distinct_question_count = after.distinct
    row.confidence_level = after.confidence
    row.review_due_at = after.review_due_at
    row.review_interval_step = after.review_step
    row.updated_at = attempt.created_at
    db.add(
        MasteryHistory(
            user_id=attempt.user_id,
            subtopic_id=question.subtopic_id,
            attempt_id=attempt.id,
            old_score=before.score,
            new_score=after.score,
            model_version=MODEL_VERSION,
            created_at=attempt.created_at,
        )
    )
    return before, after


def remediation_options(
    db: Session,
    attempt: Attempt,
    change: UserMisconception | None,
) -> tuple[Remediation, ...]:
    states = {
        row.code: row.state
        for row in db.scalars(
            select(UserMisconception).where(UserMisconception.user_id == attempt.user_id)
        )
    }
    if change is not None:
        states[change.code] = change.state
    active_codes = [code for code, state in states.items() if state in ("active", "improving")]
    if not active_codes:
        return ()

    prior_checkpoints = list(
        db.execute(
            select(QuestionVersion.question_id, SessionItem.status, SessionItem.id)
            .join(SessionItem, SessionItem.question_version_id == QuestionVersion.id)
            .join(AssessmentSession, AssessmentSession.id == SessionItem.session_id)
            .where(
                AssessmentSession.user_id == attempt.user_id, QuestionVersion.pool == "checkpoint"
            )
        )
    )
    seen = {ref for ref, _, _ in prior_checkpoints}
    open_ids = {
        ref
        for ref, status, id_ in prior_checkpoints
        if status == "open" and id_ != attempt.session_item_id
    }
    actions: list[Remediation] = []
    rules = db.scalars(
        select(Misconception)
        .where(Misconception.code.in_(active_codes), Misconception.enabled.is_(True))
        .order_by(Misconception.code)
    )
    for rule in rules:
        definition = Definition.model_validate_json(rule.definition_json)
        if any(
            reference.partition("@")[0] in open_ids or reference.partition("@")[0] not in seen
            for reference in definition.checkpoint_question_refs
        ):
            actions.append(
                Remediation(
                    rule.code, rule.title, rule.subtopic_id, rule.remediation_lesson_version_id
                )
            )
    return tuple(actions)


def latest_lesson(db: Session, topic: str) -> str | None:
    return db.scalar(
        select(LessonVersion.id)
        .join(Lesson, Lesson.id == LessonVersion.lesson_id)
        .where(Lesson.subtopic_id == topic)
        .order_by(LessonVersion.version.desc(), LessonVersion.id)
        .limit(1)
    )


def recommend(
    db: Session,
    attempt: Attempt,
    topic: str,
    mastery: MasteryState,
    misconception: UserMisconception | None,
) -> tuple[NextAction, PolicyDecision]:
    remediation = remediation_options(db, attempt, misconception)
    prerequisite: tuple[str, str] | None = None
    for parent in db.scalars(
        select(TopicPrerequisite.prerequisite_id)
        .where(
            TopicPrerequisite.topic_id == (remediation[0].topic if remediation else topic),
        )
        .order_by(TopicPrerequisite.prerequisite_id)
    ):
        parent_mastery = db.get(Mastery, (attempt.user_id, parent, MODEL_NAME))
        lesson = latest_lesson(db, parent)
        if parent_mastery is not None and parent_mastery.score <= 0.4 and lesson:
            prerequisite = (parent, lesson)
            break
    pools = set(
        db.execute(
            select(Question.type, QuestionVersion.pool)
            .join(QuestionVersion, QuestionVersion.question_id == Question.id)
            .where(Question.subtopic_id == topic)
            .distinct()
        )
    )
    seen_probes = (
        select(QuestionVersion.question_id)
        .join(SessionItem, SessionItem.question_version_id == QuestionVersion.id)
        .join(AssessmentSession, AssessmentSession.id == SessionItem.session_id)
        .where(AssessmentSession.user_id == attempt.user_id)
    )
    unused_probe = db.scalar(
        select(QuestionVersion.id)
        .join(Question, Question.id == QuestionVersion.question_id)
        .where(
            Question.subtopic_id == topic,
            Question.type == "mcq",
            QuestionVersion.pool == "diagnostic",
            Question.id.not_in(seen_probes),
        )
        .limit(1)
    )
    inputs = PolicyInput(
        topic=topic,
        mastery=mastery,
        remediation=remediation,
        missing_prerequisite=prerequisite,
        lesson_ref=latest_lesson(db, topic),
        has_probe=unused_probe is not None,
        has_practice=("mcq", "practice") in pools,
        has_sql=worker_supported() and ("sql", "practice") in pools,
    )
    action = choose_next(inputs)
    decision = PolicyDecision(
        user_id=attempt.user_id,
        trigger_attempt_id=attempt.id,
        policy_version=action.policy_version,
        model_version=MODEL_VERSION,
        input_snapshot_json=json.dumps(asdict(inputs)),
        selected_action=action.model_dump_json(),
        reason_code=action.reason_code,
        created_at=attempt.created_at,
    )
    return action, decision


def save_recommendation(
    db: Session, attempt: Attempt, decision: PolicyDecision, action: NextAction
) -> None:
    db.add(decision)
    db.flush()
    db.add(
        Recommendation(
            user_id=attempt.user_id,
            policy_decision_id=decision.id,
            action_type=action.action_type,
            subtopic_id=action.subtopic_id,
            reason=action.reason,
            created_at=attempt.created_at,
        )
    )
