"""Explainable deterministic next-action policy."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from app.services.mastery import MasteryState

POLICY_VERSION = "2"
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


class NextAction(BaseModel):
    action_type: Action
    subtopic_id: str
    reason_code: str
    reason: str
    policy_version: str = POLICY_VERSION
    misconception_code: str | None = None
    lesson_ref: str | None = None
    difficulty: str | None = None


@dataclass(frozen=True)
class Remediation:
    code: str
    title: str
    topic: str
    lesson_ref: str


@dataclass(frozen=True)
class PolicyInput:
    topic: str
    mastery: MasteryState
    remediation: tuple[Remediation, ...] = ()
    missing_prerequisite: tuple[str, str] | None = None
    lesson_ref: str | None = None
    has_probe: bool = False
    practice_difficulties: tuple[str, ...] = ()
    fresh_practice: bool = False
    review_topic: str | None = None
    has_sql: bool = False


def choose_next(inputs: PolicyInput) -> NextAction:
    state = inputs.mastery
    if inputs.missing_prerequisite and (inputs.remediation or state.band == "low"):
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

    topic = inputs.topic
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
        )
    if state.band == "low" and inputs.lesson_ref:
        return NextAction(
            action_type="RETEACH",
            subtopic_id=topic,
            reason_code="NEEDS_REVIEW",
            reason="Your recent answers suggest reviewing the concept before more practice.",
            lesson_ref=inputs.lesson_ref,
        )
    if inputs.has_sql and state.band != "high":
        return NextAction(
            action_type="SQL_PRACTICE",
            subtopic_id=topic,
            reason_code="SQL_PRACTICE_AVAILABLE",
            reason="Apply the concept to a query with immediate feedback.",
        )
    if inputs.practice_difficulties:
        order = ("medium", "easy", "hard")
        if state.band == "low" or state.confidence == "insufficient":
            order = ("easy", "medium", "hard")
        elif state.band == "high" and state.confidence == "supported":
            order = ("hard", "medium", "easy")
        actions: dict[str, Action] = {
            "easy": "PRACTICE_EASY",
            "medium": "PRACTICE_MEDIUM",
            "hard": "PRACTICE_HARD",
        }
        difficulty = next(level for level in order if level in inputs.practice_difficulties)
        if not inputs.fresh_practice:
            return NextAction(
                action_type=actions[difficulty],
                subtopic_id=topic,
                difficulty=difficulty,
                reason_code="REPEAT_PRACTICE",
                reason="You have already seen this topic's practice questions. Revisit one to reinforce the idea.",
            )
        return NextAction(
            action_type=actions[difficulty],
            subtopic_id=topic,
            difficulty=difficulty,
            reason_code="TARGETED_PRACTICE",
            reason=f"Try an available {difficulty} question to build evidence for this topic.",
        )
    if inputs.lesson_ref:
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
