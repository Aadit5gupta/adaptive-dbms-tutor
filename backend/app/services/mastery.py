"""Deterministic mastery, evidence coverage and review timing."""

from dataclasses import dataclass
from typing import Literal

MODEL_NAME = "bounded_evidence"
MODEL_VERSION = "2"
REVIEW_DAYS = (1, 3, 7, 14)
SECONDS_PER_DAY = 86_400

Confidence = Literal["insufficient", "emerging", "supported"]
ScoreBand = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class MasteryState:
    score: float = 0.5
    attempts: int = 0
    distinct: int = 0
    review_due_at: int | None = None
    review_step: int = 0

    @property
    def confidence(self) -> Confidence:
        if self.distinct >= 6:
            return "supported"
        if self.distinct >= 3:
            return "emerging"
        return "insufficient"

    @property
    def band(self) -> ScoreBand:
        if self.score <= 0.40:
            return "low"
        if self.score >= 0.70:
            return "high"
        return "medium"


@dataclass(frozen=True)
class AttemptEvidence:
    correct: bool
    first_independent_answer: bool
    recorded_at: int
    review: bool = False
    held_out: bool = False


def update_mastery(state: MasteryState, evidence: AttemptEvidence) -> MasteryState:
    if evidence.held_out:
        return state

    # Round off floating-point noise at the policy boundaries.
    score = state.score
    if evidence.first_independent_answer:
        score = round(score + 0.20 * (int(evidence.correct) - score), 12)
    step, due = state.review_step, state.review_due_at
    if evidence.first_independent_answer:
        if due is None or not evidence.correct:
            step = 0
            due = evidence.recorded_at + REVIEW_DAYS[step] * SECONDS_PER_DAY
        elif evidence.review:
            step = min(step + 1, len(REVIEW_DAYS) - 1)
            due = evidence.recorded_at + REVIEW_DAYS[step] * SECONDS_PER_DAY

    return MasteryState(
        score=score,
        attempts=state.attempts + 1,
        distinct=state.distinct + int(evidence.first_independent_answer),
        review_due_at=due,
        review_step=step,
    )
