import pytest
from app.services.mastery import SECONDS_PER_DAY, AttemptEvidence, MasteryState, update_mastery


def test_first_wrong_and_successive_correct_scores() -> None:
    assert update_mastery(MasteryState(), AttemptEvidence(False, True, 0)).score == 0.4
    mastery = MasteryState()
    for score in (0.6, 0.68, 0.744):
        mastery = update_mastery(mastery, AttemptEvidence(True, True, 0))
        assert mastery.score == score


@pytest.mark.parametrize(
    ("score", "band"),
    [
        (0.0, "low"),
        (0.40, "low"),
        (0.4001, "medium"),
        (0.6999, "medium"),
        (0.70, "high"),
        (1.0, "high"),
    ],
)
def test_policy_boundaries(score: float, band: str) -> None:
    assert MasteryState(score=score).band == band


def test_correct_improves_and_wrong_weakens_within_bounds() -> None:
    for score in (0.0, 0.4, 0.7, 1.0):
        state = MasteryState(score=score)
        wrong = update_mastery(state, AttemptEvidence(False, True, 0))
        correct = update_mastery(state, AttemptEvidence(True, True, 0))
        assert 0 <= wrong.score <= state.score <= correct.score <= 1


def test_confidence_counts_distinct_unhinted_answers_only() -> None:
    state = MasteryState(distinct=2, attempts=2)
    state = update_mastery(state, AttemptEvidence(True, False, 0))
    assert state.attempts == 3
    assert state.distinct == 2
    assert state.confidence == "insufficient"
    for confidence in ("emerging", "emerging", "emerging", "supported"):
        state = update_mastery(state, AttemptEvidence(True, True, 0))
        assert state.confidence == confidence


def test_held_out_attempt_leaves_training_state_unchanged() -> None:
    state = MasteryState()
    assert update_mastery(state, AttemptEvidence(True, True, 0, held_out=True)) is state


def test_review_uses_utc_ladder_and_ignores_non_independent_attempts() -> None:
    day = SECONDS_PER_DAY
    state = update_mastery(MasteryState(), AttemptEvidence(True, True, 0))
    assert state.review_due_at == day
    state = update_mastery(state, AttemptEvidence(True, True, day, review=True))
    assert state.review_due_at == 4 * day
    state = update_mastery(state, AttemptEvidence(True, True, 4 * day, review=True))
    assert state.review_due_at == 11 * day
    repeated = update_mastery(state, AttemptEvidence(True, False, 8 * day, review=True))
    assert repeated.review_due_at == state.review_due_at
    wrong = update_mastery(state, AttemptEvidence(False, True, 11 * day, review=True))
    assert wrong.review_due_at == 12 * day
    assert wrong.review_step == 0
