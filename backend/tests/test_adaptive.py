from app.services.adaptive import PolicyInput, Remediation, choose_next
from app.services.mastery import MasteryState


def test_remediation_precedes_generic_practice() -> None:
    rule = Remediation("KEYS-02", "Repeated reference", "relational.keys", "lesson@1")
    inputs = PolicyInput("sql.select", MasteryState(), remediation=(rule,), has_probe=True)
    action = choose_next(inputs)
    assert action.action_type == "MISCONCEPTION_REMEDIATION"
    assert action.subtopic_id == "relational.keys"
    assert action.lesson_ref == "lesson@1"


def test_high_score_requires_confidence_to_unlock_hard_practice() -> None:
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
    )
    assert choose_next(weak_evidence).action_type == "PRACTICE_EASY"
    assert choose_next(strong_evidence).action_type == "PRACTICE_HARD"


def test_missing_content_has_explainable_fallback() -> None:
    action = choose_next(PolicyInput("sql.joins", MasteryState()))
    assert action.action_type == "COMPLETE"
    assert action.reason_code == "NO_ELIGIBLE_CONTENT"


def test_policy_uses_only_available_difficulty_and_explains_repeats() -> None:
    state = MasteryState(score=0.9, distinct=6)
    available = PolicyInput(
        "sql.joins", state, practice_difficulties=("easy",), fresh_practice=True
    )
    repeated = PolicyInput("sql.joins", state, practice_difficulties=("easy",))
    assert choose_next(available).action_type == "PRACTICE_EASY"
    assert choose_next(repeated).reason_code == "REPEAT_PRACTICE"


def test_due_review_uses_real_available_topic() -> None:
    inputs = PolicyInput("relational.keys", MasteryState(), review_topic="sql.joins")
    action = choose_next(inputs)
    assert action.action_type == "MIXED_REVIEW"
    assert action.subtopic_id == "sql.joins"
