from pathlib import Path

import pytest
import yaml

from scripts.validate_content import ContentError, check_stage, load_content

from .content_fixtures import SOURCE, mcq, save


def test_empty_content_passes_structural_gate_only(foundation: Path) -> None:
    counts = load_content(foundation).counts
    assert counts.enabled_patterns == 0
    with pytest.raises(ContentError, match="S1 content gate"):
        check_stage(counts, "S1")


def test_complete_s1_fixture_passes_but_fails_s4(s1: Path) -> None:
    counts = load_content(s1).counts
    assert counts.reviewed_mcqs == 12
    assert counts.checked_sql_tasks == 1
    check_stage(counts, "S1")
    with pytest.raises(ContentError, match="S4 content gate"):
        check_stage(counts, "S4")


def test_versioned_items_are_distinct_only_by_ref(s1: Path) -> None:
    path = s1 / "content/questions/test.yaml"
    questions = yaml.safe_load(path.read_text())
    questions.append({**questions[0], "version": 2})
    save(s1, "content/questions/test.yaml", questions)
    content = load_content(s1)
    assert len(content.questions) == 14
    assert content.counts.reviewed_mcqs == 12
    questions.append(questions[0])
    save(s1, "content/questions/test.yaml", questions)
    with pytest.raises(ContentError, match="duplicate question version ordinary_0@1"):
        load_content(s1)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("pool", "detector", "practice"),
        ("version", True, "valid integer"),
        ("verified_by", None, "require author"),
        ("subtopic_id", "sql.unknown", "unknown subtopic"),
        ("source", {**SOURCE, "reproduced_book_text": True}, "requires source_section_clearance"),
    ],
)
def test_invalid_question_has_actionable_error(
    foundation: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    save(
        foundation,
        "content/questions/test.yaml",
        [
            {**mcq("question", "sql.select"), field: value},
        ],
    )
    with pytest.raises(ContentError, match=message):
        load_content(foundation)


@pytest.mark.parametrize(
    ("field", "invalid", "message"),
    [
        ("checkpoint_question_refs", ["keys_checkpoint_0@1"], "two checkpoints"),
        ("detector_question_refs", ["keys_detector_0@1"], "distinct detectors"),
        ("remediation_lesson_ref", "missing@1", "missing remediation lesson"),
        ("checkpoint_question_refs", ["ordinary_0@1"], "reserved checkpoint"),
    ],
)
def test_disabled_content_cannot_satisfy_enabled_gate(
    s1: Path,
    field: str,
    invalid: object,
    message: str,
) -> None:
    path = s1 / "content/misconceptions.yaml"
    rules = yaml.safe_load(path.read_text())
    rules[0][field] = invalid
    save(s1, "content/misconceptions.yaml", rules)
    with pytest.raises(ContentError, match=message):
        load_content(s1)


def test_detector_versions_do_not_count_as_independent(s1: Path) -> None:
    questions_path = s1 / "content/questions/test.yaml"
    questions = yaml.safe_load(questions_path.read_text())
    questions.append({**questions[4], "version": 2})
    save(s1, "content/questions/test.yaml", questions)
    rules = yaml.safe_load((s1 / "content/misconceptions.yaml").read_text())
    rules[0]["detector_question_refs"] = ["keys_detector_0@1", "keys_detector_0@2"]
    save(s1, "content/misconceptions.yaml", rules)
    with pytest.raises(ContentError, match="detector logical IDs must be distinct"):
        load_content(s1)


def test_invalid_sql_expected_result_fails(s1: Path) -> None:
    (s1 / "tests/fixtures/expected/data_1.json").write_text("[[2]]")
    with pytest.raises(ContentError, match="reference query does not match expected"):
        load_content(s1)


def test_prerequisite_cycle_fails(foundation: Path) -> None:
    save(
        foundation,
        "content/curriculum/prerequisites.yaml",
        [
            {"subtopic_id": "sql.select", "prerequisite_id": "sql.joins"},
            {"subtopic_id": "sql.joins", "prerequisite_id": "sql.select"},
        ],
    )
    with pytest.raises(ContentError, match="cycle"):
        load_content(foundation)
