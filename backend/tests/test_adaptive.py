from dataclasses import replace

from app.services.adaptive import PolicyInput, Remediation, choose_next
from app.services.mastery import MasteryState


def test_remediation_precedes_generic_practice() -> None:
    rule = Remediation("KEYS-02", "Repeated reference", "relational.keys", "lesson@1")
    inputs = PolicyInput("sql.select", MasteryState(), remediation=(rule,), has_probe=True)
    action = choose_next(inputs)
    assert action.action_type == "MISCONCEPTION_REMEDIATION"
    assert action.subtopic_id == "relational.keys"
    assert action.lesson_ref == "lesson@1"


def test_hard_practice_requires_confidence_and_medium_evidence() -> None:
    weak_evidence = PolicyInput(
        "sql.joins",
        MasteryState(score=0.9, distinct=1),
        practice_difficulties=("easy", "hard"),
        fresh_practice=True,
    )
    strong_evidence = PolicyInput(
        "sql.joins",
        MasteryState(score=0.9, distinct=6),
        practice_difficulties=("easy", "hard"),
        fresh_practice=True,
        easy_correct=3,
        medium_correct=2,
        highest_available="hard",
    )
    assert choose_next(weak_evidence).action_type == "PRACTICE_EASY"
    assert choose_next(strong_evidence).action_type == "PRACTICE_HARD"
    assert choose_next(replace(strong_evidence, easy_correct=1)).action_type == "PRACTICE_EASY"
    struggling_at_medium = replace(
        strong_evidence,
        mastery=MasteryState(score=0.61, distinct=6),
        medium_correct=0,
        practice_difficulties=("medium", "hard"),
    )
    assert choose_next(struggling_at_medium).action_type == "PRACTICE_MEDIUM"


def test_missing_content_has_explainable_fallback() -> None:
    action = choose_next(PolicyInput("sql.joins", MasteryState()))
    assert action.action_type == "COMPLETE"
    assert action.reason_code == "NO_ELIGIBLE_CONTENT"


def test_policy_uses_only_available_difficulty_and_ends_repeat_loops() -> None:
    state = MasteryState(score=0.9, distinct=6)
    available = PolicyInput(
        "sql.joins", state, practice_difficulties=("easy",), fresh_practice=True
    )
    repeated = PolicyInput("sql.joins", state, practice_difficulties=("easy",))
    assert choose_next(available).action_type == "PRACTICE_EASY"
    assert choose_next(repeated).reason_code == "AVAILABLE_CONTENT_EXHAUSTED"


def test_due_review_uses_real_available_topic() -> None:
    inputs = PolicyInput("relational.keys", MasteryState(), review_topic="sql.joins")
    action = choose_next(inputs)
    assert action.action_type == "MIXED_REVIEW"
    assert action.subtopic_id == "sql.joins"


def test_simulation_is_deterministic_and_labeled_synthetic() -> None:
    from scripts.simulate_policy import simulate

    result = simulate()
    assert result == simulate()
    assert result["data"] == "synthetic"
    outcomes = result["outcomes"]
    assert isinstance(outcomes, dict)
    assert outcomes["three_independent_correct"]["scores"] == [0.6, 0.68, 0.744]
    assert outcomes["one_correct_repeated"]["distinct_answers"] == 1
    assert outcomes["two_independent_detector_errors"]["action"] == "MISCONCEPTION_REMEDIATION"


def test_high_score_cannot_skip_unassessed_prerequisite_or_unsupported_difficulty() -> None:
    from app.services.adaptive import Alternative

    ready = PolicyInput(
        "sql.select",
        MasteryState(score=0.9, distinct=5, attempts=5),
        easy_correct=3,
        missing_prerequisite=("relational.relations", "relations@1"),
        alternative=Alternative("sql.joins", "Joins", "joins@1"),
    )
    assert choose_next(ready).reason_code == "PREREQUISITE"
    assert choose_next(replace(ready, missing_prerequisite=None)).reason_code == "ADVANCE_TOPIC"
    limited = PolicyInput(
        "sql.joins",
        MasteryState(score=0.9, distinct=6, attempts=6),
        easy_correct=4,
        practice_difficulties=("hard",),
        fresh_practice=True,
        highest_available="hard",
        alternative=Alternative("sql.null", "NULL", "null@1"),
    )
    assert choose_next(limited).reason_code == "EXPLORE_NEXT_TOPIC"
