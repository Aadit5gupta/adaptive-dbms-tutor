from pathlib import Path

from app.db.models import QuestionOption, QuestionVersion, SessionItem
from app.services.misconceptions import Signal, evaluate_hypothesis, identify_signal

from scripts.validate_content import load_content


def test_hypothesis_requires_distinct_detectors_and_two_clean_checkpoints() -> None:
    first = Signal("question_a", "detector_wrong")
    second = Signal("question_b", "detector_wrong")
    checkpoint = Signal("checkpoint_a", "checkpoint_correct")
    assert evaluate_hypothesis([]).state is None
    assert evaluate_hypothesis([first, first]).state == "possible"
    assert evaluate_hypothesis([first, second]).state == "active"
    signs = [first, second, checkpoint]
    assert evaluate_hypothesis([*signs, checkpoint]).state == "improving"
    assert (
        evaluate_hypothesis([*signs, Signal("checkpoint_b", "checkpoint_wrong")]).state
        == "improving"
    )
    assert (
        evaluate_hypothesis([*signs, Signal("checkpoint_c", "checkpoint_correct")]).state
        == "resolved"
    )


def test_unrelated_mapping_and_revealing_hints_do_not_count(s1: Path) -> None:
    rule = load_content(s1).rules["KEYS-02"]
    question = QuestionVersion(id="keys_detector_0@1", pool="practice")
    wrong = QuestionOption(is_correct=False, misconception_code="KEYS-02")
    snap = SessionItem(revealing_hint_used=False)
    assert identify_signal(rule, snap, question, wrong) == "detector_wrong"
    wrong.misconception_code = None
    assert identify_signal(rule, snap, question, wrong) is None
    wrong.misconception_code = "KEYS-02"
    snap.revealing_hint_used = True
    assert identify_signal(rule, snap, question, wrong) is None


def test_checkpoint_has_to_belong_to_the_remediation_session(s1: Path) -> None:
    rule = load_content(s1).rules["KEYS-02"]
    question = QuestionVersion(id="keys_checkpoint_0@1", pool="checkpoint")
    choice = QuestionOption(is_correct=True)
    item = SessionItem(revealing_hint_used=False)
    assert identify_signal(rule, item, question, choice) is None
    item.remediation_code = "KEYS-02"
    assert identify_signal(rule, item, question, choice) == "checkpoint_correct"
    assert (
        identify_signal(rule, item, question, QuestionOption(is_correct=False))
        == "checkpoint_wrong"
    )
    item.revealing_hint_used = True
    assert identify_signal(rule, item, question, choice) is None
