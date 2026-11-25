"""Transactional learner state transitions shared by MCQ and SQL grading."""

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field, replace

from sqlalchemy import literal_column, select
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
    Topic,
    TopicPrerequisite,
    UserMisconception,
)
from app.services.adaptive import (
    Alternative,
    NextAction,
    PolicyInput,
    Remediation,
    choose_next,
    eligible_difficulty,
    topic_ready,
)
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
            Attempt.context.not_in(("pre_test_a", "post_test_b")),
        )
        .limit(1)
    )
    return earlier is None


def state_from_row(row: Mastery | None) -> MasteryState:
    if row is None:
        return MasteryState()
    return MasteryState(
        score=row.score,
        attempts=row.attempts_count,
        distinct=row.distinct_question_count,
        review_due_at=row.review_due_at,
        review_step=row.review_interval_step,
    )


def mastery_for(
    db: Session, attempt: Attempt, question: Question
) -> tuple[MasteryState, MasteryState]:
    key = (attempt.user_id, question.subtopic_id, MODEL_NAME)
    row = db.get(Mastery, key)
    before = state_from_row(row)
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
    user_id: str,
    change: UserMisconception | None,
    submitted_item: str | None,
) -> tuple[Remediation, ...]:
    states = {
        row.code: row.state
        for row in db.scalars(select(UserMisconception).where(UserMisconception.user_id == user_id))
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
            .where(AssessmentSession.user_id == user_id, QuestionVersion.pool == "checkpoint")
        )
    )
    seen = {ref for ref, _, _ in prior_checkpoints}
    open_ids = {
        ref for ref, status, id_ in prior_checkpoints if status == "open" and id_ != submitted_item
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


TIERS = ("easy", "medium", "hard")


@dataclass
class Availability:
    practice: set[str] = field(default_factory=set)
    fresh: set[str] = field(default_factory=set)
    review: bool = False
    diagnostic: bool = False
    sql: list[tuple[int, str]] = field(default_factory=list)

    @property
    def sql_id(self) -> str | None:
        return min(self.sql)[1] if self.sql else None

    @property
    def highest(self) -> str:
        return next((tier for tier in reversed(TIERS) if tier in self.practice), "easy")


def attempts_by_question(
    db: Session, user_id: str, pending: Attempt | None
) -> tuple[set[str], dict[str, dict[str, int]]]:
    query = (
        select(
            QuestionVersion.question_id,
            Question.subtopic_id,
            QuestionVersion.difficulty,
            Attempt.correct,
            Attempt.hint_used,
            Attempt.context,
        )
        .join(QuestionVersion, QuestionVersion.id == Attempt.question_version_id)
        .join(Question, Question.id == QuestionVersion.question_id)
        .where(Attempt.user_id == user_id, Attempt.context.not_in(("pre_test_a", "post_test_b")))
        .order_by(literal_column("attempts.rowid"))
    )
    records = [
        (ref, topic, difficulty, passed, hinted, context)
        for ref, topic, difficulty, passed, hinted, context in db.execute(query)
    ]
    if pending is not None:
        version = db.get(QuestionVersion, pending.question_version_id)
        assert version is not None
        question = db.get(Question, version.question_id)
        assert question is not None
        records.append(
            (
                question.id,
                question.subtopic_id,
                version.difficulty,
                pending.correct,
                pending.hint_used,
                pending.context,
            )
        )
    answered: set[str] = set()
    correct: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for ref, topic, difficulty, passed, hinted, context in records:
        if (
            ref not in answered
            and passed
            and not hinted
            and context in ("diagnostic", "practice", "review")
        ):
            correct[topic][difficulty] += 1
        answered.add(ref)
    return answered, correct


def activity_inventory(
    db: Session, user_id: str, answered: set[str], submitted_item: str | None
) -> dict[str, Availability]:
    allocated = list(
        db.execute(
            select(
                SessionItem.id,
                AssessmentSession.id,
                AssessmentSession.kind,
                AssessmentSession.status,
                SessionItem.status,
                QuestionVersion.question_id,
                Question.subtopic_id,
                QuestionVersion.difficulty,
            )
            .join(AssessmentSession, AssessmentSession.id == SessionItem.session_id)
            .join(QuestionVersion, QuestionVersion.id == SessionItem.question_version_id)
            .join(Question, Question.id == QuestionVersion.question_id)
            .where(AssessmentSession.user_id == user_id)
        )
    )
    seen = {row[5] for row in allocated}
    pending_diagnostics: set[str] = set()
    sessions: dict[str, list[tuple[str, str, str, bool, str]]] = defaultdict(list)
    for item_id, sid, kind, session_status, status, ref, topic, difficulty in allocated:
        pending = status == "open" and item_id != submitted_item
        if session_status != "open":
            continue
        if kind == "diagnostic" and pending and ref not in answered:
            pending_diagnostics.add(ref)
        if kind in ("practice", "review"):
            sessions[sid].append((topic, difficulty, ref, pending, kind))
    pending_practice: set[str] = set()
    pending_review: set[str] = set()
    for items in sessions.values():
        open_refs = {ref for _, _, ref, pending, _ in items if pending}
        if not open_refs or open_refs & answered:
            continue
        topics = {item[0] for item in items}
        if len(topics) == 1 and items[0][4] == "review":
            pending_review.update(open_refs)
        if len(topics) == 1 and len({item[1] for item in items}) == 1 and items[0][4] == "practice":
            pending_practice.update(open_refs)

    grouped: dict[str, Availability] = defaultdict(Availability)
    newest: set[str] = set()
    sql_supported = worker_supported()
    for ref, topic, kind, pool, difficulty in db.execute(
        select(
            Question.id,
            Question.subtopic_id,
            Question.type,
            QuestionVersion.pool,
            QuestionVersion.difficulty,
        )
        .join(QuestionVersion, QuestionVersion.question_id == Question.id)
        .where(QuestionVersion.pool.in_(("practice", "diagnostic")))
        .order_by(Question.id, QuestionVersion.version.desc())
    ):
        if ref in newest:
            continue
        newest.add(ref)
        content = grouped[topic]
        if kind == "sql" and sql_supported and ref not in answered:
            content.sql.append((TIERS.index(difficulty), ref))
        if kind != "mcq":
            continue
        if pool == "diagnostic":
            content.diagnostic |= ref not in seen or ref in pending_diagnostics
        if pool == "practice":
            content.practice.add(difficulty)
            if ref not in seen or ref in pending_practice:
                content.fresh.add(difficulty)
            content.review |= ref not in seen or ref in pending_review
    return grouped


def learner_snapshot(
    db: Session,
    attempt: Attempt,
    topic: str,
    mastery: MasteryState,
    now: int,
    *,
    change: UserMisconception | None = None,
    pending: bool = False,
) -> PolicyInput:
    reminder = attempt.session_item_id if pending else None
    user_id = attempt.user_id
    remediation = remediation_options(db, user_id, change, reminder)
    rows = {
        row.subtopic_id: row
        for row in db.scalars(
            select(Mastery).where(Mastery.user_id == user_id, Mastery.model_name == MODEL_NAME)
        )
    }
    states = {key: state_from_row(row) for key, row in rows.items()}
    states[topic] = mastery
    answered, correct = attempts_by_question(db, user_id, attempt if pending else None)
    inventory = activity_inventory(db, user_id, answered, reminder)
    prerequisites: dict[str, list[str]] = defaultdict(list)
    for child, parent in db.execute(
        select(TopicPrerequisite.topic_id, TopicPrerequisite.prerequisite_id).order_by(
            TopicPrerequisite.prerequisite_id
        )
    ):
        prerequisites[child].append(parent)

    latest: dict[str, str] = {}
    for id_, ref in db.execute(
        select(Lesson.subtopic_id, LessonVersion.id)
        .join(Lesson, Lesson.id == LessonVersion.lesson_id)
        .order_by(LessonVersion.version.desc(), LessonVersion.id)
    ):
        latest.setdefault(id_, ref)

    def for_topic(id_: str) -> PolicyInput:
        content = inventory[id_]
        successes = correct.get(id_, {})
        return PolicyInput(
            topic=id_,
            mastery=states.get(id_, MasteryState()),
            lesson_ref=latest.get(id_),
            has_probe=content.diagnostic,
            practice_difficulties=tuple(sorted(content.fresh or content.practice)),
            fresh_practice=bool(content.fresh),
            has_sql=bool(content.sql),
            sql_id=content.sql_id,
            easy_correct=successes.get("easy", 0),
            medium_correct=successes.get("medium", 0),
            hard_correct=successes.get("hard", 0),
            highest_available=content.highest,
        )

    focus = for_topic(topic)
    reteach_lesson = db.scalar(
        select(Misconception.remediation_lesson_version_id)
        .join(UserMisconception, UserMisconception.code == Misconception.code)
        .where(
            UserMisconception.user_id == user_id,
            UserMisconception.state.in_(("possible", "active", "improving")),
            Misconception.subtopic_id == topic,
            Misconception.enabled.is_(True),
        )
        .order_by(UserMisconception.last_seen_at.desc(), Misconception.code)
        .limit(1)
    )
    if change is not None and change.state != "resolved":
        rule = db.get(Misconception, change.code)
        if rule is not None and rule.enabled and rule.subtopic_id == topic:
            reteach_lesson = rule.remediation_lesson_version_id
    parent_of = remediation[0].topic if remediation else topic
    missing = next(
        (
            (parent, latest[parent])
            for parent in prerequisites[parent_of]
            if parent in latest
            and (
                (parent in states and states[parent].band == "low")
                or (
                    not remediation
                    and topic_ready(focus)
                    and (parent not in states or states[parent].distinct == 0)
                )
            )
        ),
        None,
    )
    due = sorted(
        (state.review_due_at, target)
        for target, state in states.items()
        if state.review_due_at is not None and state.review_due_at <= now
    )
    review = next((target for _, target in due if inventory[target].review), None)

    candidates = []
    for position, row in enumerate(
        db.scalars(select(Topic).order_by(literal_column("topics.rowid")))
    ):
        candidate = row.id
        if candidate == topic or any(
            parent not in states or states[parent].distinct == 0 or states[parent].band == "low"
            for parent in prerequisites[candidate]
        ):
            continue
        option = for_topic(candidate)
        content = inventory[candidate]
        difficulty = eligible_difficulty(option)
        if not (content.diagnostic or difficulty or content.sql_id):
            continue
        if topic_ready(option) and not content.diagnostic and not content.sql_id:
            continue
        group = (
            0
            if candidate in states and option.mastery.band == "low"
            else int(candidate in states) + 1
        )
        recent = rows[candidate].updated_at if candidate in rows else 0
        candidates.append(
            (
                (group, option.mastery.score, -recent, position),
                Alternative(
                    candidate,
                    row.title,
                    option.lesson_ref if group < 2 else None,
                    content.diagnostic,
                    difficulty,
                    content.sql_id,
                ),
            )
        )
    alternative = min(candidates, key=lambda item: item[0])[1] if candidates else None
    exhausted_remediation = (
        attempt.context == "checkpoint"
        and not remediation
        and (
            (change is not None and change.state != "resolved")
            or (
                not pending
                and db.scalar(
                    select(UserMisconception.code)
                    .join(SessionItem, SessionItem.remediation_code == UserMisconception.code)
                    .where(
                        SessionItem.id == attempt.session_item_id,
                        UserMisconception.user_id == user_id,
                        UserMisconception.state.in_(("active", "improving")),
                    )
                )
                is not None
            )
        )
    )
    return replace(
        focus,
        remediation=remediation,
        reteach_lesson_ref=reteach_lesson,
        missing_prerequisite=missing,
        review_topic=review,
        last_correct=attempt.correct,
        alternative=alternative,
        review_waiting=bool(due),
        exhausted_remediation=exhausted_remediation,
    )


def recommend(
    db: Session,
    attempt: Attempt,
    topic: str,
    mastery: MasteryState,
    misconception: UserMisconception | None,
) -> tuple[NextAction, PolicyDecision]:
    inputs = learner_snapshot(
        db, attempt, topic, mastery, attempt.created_at, change=misconception, pending=True
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
