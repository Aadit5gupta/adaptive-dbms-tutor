"""Independent misconception evidence and conservative remediation transitions."""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Attempt,
    Misconception,
    MisconceptionEvidence,
    QuestionOption,
    QuestionVersion,
    SessionItem,
    UserMisconception,
)
from content.schemas.models import Misconception as Definition

Status = Literal["possible", "active", "improving", "resolved"]
EvidenceType = Literal["detector_wrong", "checkpoint_correct", "checkpoint_wrong"]


@dataclass(frozen=True)
class Signal:
    logical_id: str
    kind: EvidenceType


@dataclass(frozen=True)
class Hypothesis:
    state: Status | None
    evidence_count: int


def evaluate_hypothesis(signals: list[Signal], minimum: int = 2) -> Hypothesis:
    state: Status | None = None
    seen: set[str] = set()
    detectors: set[str] = set()
    checkpoints: set[str] = set()
    for signal in signals:
        if signal.logical_id in seen:
            continue
        seen.add(signal.logical_id)
        if signal.kind == "detector_wrong":
            if state == "resolved":
                detectors.clear()
                checkpoints.clear()
                state = None
            detectors.add(signal.logical_id)
            if state in (None, "possible"):
                state = "active" if len(detectors) >= minimum else "possible"
        elif signal.kind == "checkpoint_correct" and state in ("active", "improving"):
            checkpoints.add(signal.logical_id)
            state = "resolved" if len(checkpoints) >= 2 else "improving"
    return Hypothesis(state=state, evidence_count=len(detectors))


def identify_signal(
    definition: Definition,
    item: SessionItem,
    question: QuestionVersion,
    option: QuestionOption,
) -> EvidenceType | None:
    if item.revealing_hint_used or not definition.enabled:
        return None
    if (
        item.remediation_code == definition.code
        and question.pool == "checkpoint"
        and question.id in definition.checkpoint_question_refs
    ):
        return "checkpoint_correct" if option.is_correct else "checkpoint_wrong"
    if (
        not option.is_correct
        and option.misconception_code == definition.code
        and question.id in definition.detector_question_refs
        and question.pool in ("practice", "diagnostic")
    ):
        return "detector_wrong"
    return None


def update_misconception(
    db: Session,
    attempt: Attempt,
    item: SessionItem,
    question: QuestionVersion,
    option: QuestionOption,
) -> UserMisconception | None:
    code = item.remediation_code or option.misconception_code
    if code is None:
        return None
    rule = db.get(Misconception, code)
    if rule is None or not rule.enabled:
        return None
    definition = Definition.model_validate_json(rule.definition_json)
    signal = identify_signal(definition, item, question, option)
    if signal is None:
        return None
    # Once this answer has been graded, a later attempt can use the feedback.
    # Treat it as practice regardless of the earlier answer's correctness.
    if (
        signal == "detector_wrong"
        and db.scalar(
            select(Attempt.id)
            .join(QuestionVersion, QuestionVersion.id == Attempt.question_version_id)
            .where(
                Attempt.user_id == attempt.user_id,
                QuestionVersion.question_id == question.question_id,
            )
            .limit(1)
        )
        is not None
    ):
        return None
    current = db.get(UserMisconception, (attempt.user_id, code))
    if signal != "detector_wrong" and (
        current is None or current.state not in ("active", "improving")
    ):
        return None
    history = list(
        db.scalars(
            select(MisconceptionEvidence)
            .where(
                MisconceptionEvidence.user_id == attempt.user_id,
                MisconceptionEvidence.code == code,
            )
            .order_by(MisconceptionEvidence.id)
        )
    )
    if any(evidence.question_id == question.question_id for evidence in history):
        return None

    reasons = {
        "detector_wrong": "Selected a reviewed distractor linked to this hypothesis.",
        "checkpoint_correct": "Correct independent response to a reserved checkpoint.",
        "checkpoint_wrong": "The reserved checkpoint still needs practice.",
    }
    evidence = MisconceptionEvidence(
        user_id=attempt.user_id,
        code=code,
        attempt_id=attempt.id,
        question_id=question.question_id,
        question_version_id=question.id,
        evidence_type=signal,
        reason=reasons[signal],
        created_at=attempt.created_at,
    )
    db.add(evidence)
    kinds: dict[str, EvidenceType] = {
        "detector_wrong": "detector_wrong",
        "checkpoint_correct": "checkpoint_correct",
        "checkpoint_wrong": "checkpoint_wrong",
    }
    signals = [Signal(row.question_id, kinds[row.evidence_type]) for row in history]
    outcome = evaluate_hypothesis(
        [*signals, Signal(question.question_id, signal)],
        definition.evidence_rule.min_distinct_logical_questions,
    )
    if outcome.state is None:
        return None
    return db.merge(
        UserMisconception(
            user_id=attempt.user_id,
            code=code,
            state=outcome.state,
            evidence_count=outcome.evidence_count,
            last_seen_at=attempt.created_at,
            resolved_at=attempt.created_at if outcome.state == "resolved" else None,
        )
    )
