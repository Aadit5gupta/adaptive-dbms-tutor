"""Explainable deterministic next-action policy."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from app.services.mastery import MasteryState

POLICY_VERSION = "3"
Difficulty = Literal["easy", "medium", "hard"]
Action = Literal[
    "DIAGNOSTIC",
    "LEARN",
    "RETEACH",
    "MISCONCEPTION_REMEDIATION",
    "PRACTICE_EASY",
    "PRACTICE_MEDIUM",
    "PRACTICE_HARD",
    "SQL_PRACTICE",
    "MIXED_REVIEW",
    "REVIEW_LATER",
    "COMPLETE",
]
PRACTICE: dict[str, Action] = {
    "easy": "PRACTICE_EASY",
    "medium": "PRACTICE_MEDIUM",
    "hard": "PRACTICE_HARD",
}


class NextAction(BaseModel):
    action_type: Action
    subtopic_id: str
    reason_code: str
    reason: str
    policy_version: str = POLICY_VERSION
    misconception_code: str | None = None
    lesson_ref: str | None = None
    difficulty: str | None = None
    question_id: str | None = None
    fresh: bool = False


@dataclass(frozen=True)
class Remediation:
    code: str
    title: str
    topic: str
    lesson_ref: str


@dataclass(frozen=True)
class Alternative:
    topic: str
    title: str
    lesson_ref: str | None
    has_probe: bool = False
    difficulty: str | None = None
    sql_id: str | None = None


@dataclass(frozen=True)
class PolicyInput:
    topic: str
    mastery: MasteryState
    remediation: tuple[Remediation, ...] = ()
    missing_prerequisite: tuple[str, str] | None = None
    lesson_ref: str | None = None
    reteach_lesson_ref: str | None = None
    has_probe: bool = False
    practice_difficulties: tuple[str, ...] = ()
    fresh_practice: bool = False
    review_topic: str | None = None
    has_sql: bool = False
    sql_id: str | None = None
    easy_correct: int = 0
    medium_correct: int = 0
    hard_correct: int = 0
    last_correct: bool = True
    highest_available: str = "easy"
    alternative: Alternative | None = None
    review_waiting: bool = False
    exhausted_remediation: bool = False


def eligible_difficulty(inputs: PolicyInput) -> str | None:
    state = inputs.mastery
    available = inputs.practice_difficulties
    if not inputs.fresh_practice:
        return None
    medium_ready = state.confidence != "insufficient" and inputs.easy_correct >= 2
    hard_ready = (
        medium_ready
        and state.confidence == "supported"
        and state.band == "high"
        and inputs.medium_correct >= 2
    )
    if hard_ready and "hard" in available:
        return "hard"
    if medium_ready and state.band != "low" and "medium" in available:
        return "medium"
    if "easy" in available:
        return "easy"
    return None


def topic_ready(inputs: PolicyInput) -> bool:
    mastery = inputs.mastery
    if mastery.band != "high" or mastery.confidence == "insufficient" or inputs.easy_correct < 2:
        return False
    if inputs.highest_available == "hard":
        return (
            mastery.confidence == "supported"
            and inputs.medium_correct >= 2
            and inputs.hard_correct >= 2
        )
    return inputs.highest_available == "easy" or inputs.medium_correct >= 2


def choose_next(inputs: PolicyInput) -> NextAction:
    state = inputs.mastery
    topic = inputs.topic
    ready = topic_ready(inputs)
    if inputs.missing_prerequisite and (inputs.remediation or state.band == "low" or ready):
        prerequisite, lesson = inputs.missing_prerequisite
        return NextAction(
            action_type="LEARN",
            subtopic_id=prerequisite,
            reason_code="PREREQUISITE",
            reason="Review a prerequisite before trying this concept again.",
            lesson_ref=lesson,
        )
    if inputs.remediation:
        rule = inputs.remediation[0]
        return NextAction(
            action_type="MISCONCEPTION_REMEDIATION",
            subtopic_id=rule.topic,
            reason_code="INDEPENDENT_MISCONCEPTION_EVIDENCE",
            reason=f"Different answers suggest you may be applying this idea: {rule.title}. Try a worked example and checkpoints.",
            misconception_code=rule.code,
            lesson_ref=rule.lesson_ref,
        )
    reteach_lesson = inputs.reteach_lesson_ref or inputs.lesson_ref
    if inputs.exhausted_remediation and reteach_lesson:
        return NextAction(
            action_type="RETEACH",
            subtopic_id=topic,
            reason_code="CHECKPOINTS_EXHAUSTED",
            reason="The available checkpoints are used and the idea still needs work. Revisit the explanation and practice.",
            lesson_ref=reteach_lesson,
        )
    if not inputs.last_correct and state.band == "low" and reteach_lesson:
        return NextAction(
            action_type="RETEACH",
            subtopic_id=topic,
            reason_code="NEEDS_REVIEW",
            reason="Your recent answers suggest reviewing the concept before more practice.",
            lesson_ref=reteach_lesson,
            difficulty="easy"
            if inputs.fresh_practice and "easy" in inputs.practice_difficulties
            else None,
            fresh=inputs.fresh_practice and "easy" in inputs.practice_difficulties,
        )
    if state.confidence == "insufficient" and inputs.has_probe:
        return NextAction(
            action_type="DIAGNOSTIC",
            subtopic_id=topic,
            reason_code="NEEDS_EVIDENCE",
            reason="A few more independent answers will help clarify what to practice.",
        )
    if inputs.review_topic:
        return NextAction(
            action_type="MIXED_REVIEW",
            subtopic_id=inputs.review_topic,
            reason_code="REVIEW_DUE",
            reason="This topic is due for revision and has a fresh practice question.",
            fresh=True,
        )

    difficulty = eligible_difficulty(inputs)
    if not ready and difficulty is not None:
        return NextAction(
            action_type=PRACTICE[difficulty],
            subtopic_id=topic,
            difficulty=difficulty,
            reason_code="TARGETED_PRACTICE",
            reason=f"Try an available {difficulty} question to build evidence for this topic.",
            fresh=True,
        )

    if (
        inputs.has_sql
        and inputs.sql_id
        and state.band != "low"
        and (not ready or inputs.alternative is None)
    ):
        return NextAction(
            action_type="SQL_PRACTICE",
            subtopic_id=topic,
            question_id=inputs.sql_id,
            reason_code="SQL_PRACTICE_AVAILABLE",
            reason="Apply this concept to an unattempted SQL exercise.",
        )
    if inputs.alternative:
        next_ = inputs.alternative
        reason = (
            f"Your independent work supports moving on to {next_.title}."
            if ready
            else f"Fresh practice at a suitable level is unavailable here. Continue with {next_.title} while this topic remains open for review."
        )
        action: Action = "SQL_PRACTICE"
        if next_.lesson_ref:
            action = "LEARN"
        elif next_.has_probe:
            action = "DIAGNOSTIC"
        elif next_.difficulty:
            action = PRACTICE[next_.difficulty]
        return NextAction(
            action_type=action,
            subtopic_id=next_.topic,
            reason_code="ADVANCE_TOPIC" if ready else "EXPLORE_NEXT_TOPIC",
            reason=reason,
            lesson_ref=next_.lesson_ref,
            difficulty=next_.difficulty,
            question_id=next_.sql_id if action == "SQL_PRACTICE" else None,
            fresh=next_.difficulty is not None,
        )
    if inputs.review_waiting:
        return NextAction(
            action_type="REVIEW_LATER",
            subtopic_id=topic,
            reason_code="REVIEW_NO_FRESH_ITEMS",
            reason="Revision is due, and this bank has no fresh eligible review questions. Open Progress for optional revision.",
        )
    if inputs.practice_difficulties or state.attempts:
        return NextAction(
            action_type="COMPLETE",
            subtopic_id=topic,
            reason_code="AVAILABLE_CONTENT_EXHAUSTED",
            reason="You have reached the end of the fresh activities currently available to you. Browse lessons or revisit a topic for revision.",
        )
    if inputs.lesson_ref and state.band == "low":
        return NextAction(
            action_type="LEARN",
            subtopic_id=topic,
            reason_code="LESSON_AVAILABLE",
            reason="A reviewed lesson is available for this topic.",
            lesson_ref=inputs.lesson_ref,
        )
    return NextAction(
        action_type="COMPLETE",
        subtopic_id=topic,
        reason_code="NO_ELIGIBLE_CONTENT",
        reason="There is no reviewed activity for this topic yet. You can choose another topic.",
    )
