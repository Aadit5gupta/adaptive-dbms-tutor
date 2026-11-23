import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.validate_content import ROOT, ContentError, check_stage, load_content

SOURCE = {"kind": "authored", "factual_reference_url": "https://example.invalid/dbms"}
APPROVED = {
    "review_status": "author_verified",
    "author": "Synthetic test author",
    "verified_by": "Synthetic test reviewer",
    "verified_on": "2026-11-23",
    "second_review": False,
    "ai_assisted": False,
    "source": SOURCE,
}


def save(root: Path, filename: str, value: Any) -> Path:
    path = root / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value), encoding="utf-8")
    return path


def mcq(id_: str, topic: str, pool: str = "practice", code: str | None = None) -> dict[str, Any]:
    return {
        **APPROVED,
        "id": id_,
        "type": "mcq",
        "subtopic_id": topic,
        "version": 1,
        "pool": pool,
        "difficulty": "easy",
        "stem": "Synthetic question",
        "explanation": "Synthetic explanation",
        "options": [
            {"text": "A", "correct": True},
            {"text": "B", "correct": False, "misconception_code": code},
            {"text": "C", "correct": False},
            {"text": "D", "correct": False},
        ],
    }


@pytest.fixture
def foundation(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "content/curriculum", tmp_path / "content/curriculum")
    return tmp_path


@pytest.fixture
def s1(foundation: Path) -> Path:
    questions = [mcq(f"ordinary_{i}", "sql.select") for i in range(4)]
    lessons = []
    rules = []
    for slug, topic, code in (
        ("keys", "relational.keys", "KEYS-02"),
        ("joins", "sql.joins", "SQL-JOIN-01"),
    ):
        detectors = [f"{slug}_detector_{i}" for i in range(2)]
        checkpoints = [f"{slug}_checkpoint_{i}" for i in range(2)]
        questions.extend(mcq(id_, topic, code=code) for id_ in detectors)
        questions.extend(mcq(id_, topic, pool="checkpoint") for id_ in checkpoints)
        lessons.append(
            {
                **APPROVED,
                "id": slug,
                "version": 1,
                "subtopic_id": topic,
                "title": slug,
                "body_markdown": "Synthetic lesson",
            }
        )
        rules.append(
            {
                **APPROVED,
                "code": code,
                "subtopic_id": topic,
                "enabled": True,
                "name": "Synthetic misconception",
                "explanation": "Synthetic explanation",
                "evidence_rule": {
                    "min_distinct_logical_questions": 2,
                    "ignore_after_revealing_hint": True,
                },
                "detector_question_refs": [f"{id_}@1" for id_ in detectors],
                "checkpoint_question_refs": [f"{id_}@1" for id_ in checkpoints],
                "remediation_lesson_ref": f"{slug}@1",
                "retrieval_query": slug,
            }
        )
    fixtures = [f"content/sql_fixtures/data_{i}.sql" for i in range(2)]
    results = []
    for i, fixture in enumerate(fixtures):
        fixture_path = foundation / fixture
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(f"CREATE TABLE t(n); INSERT INTO t VALUES ({i});")
        result = f"tests/fixtures/expected/data_{i}.json"
        result_path = foundation / result
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps([[i]]))
        results.append({"fixture": fixture, "expected_result_file": result})
    questions.append(
        {
            **APPROVED,
            "id": "sql_fixture",
            "type": "sql",
            "version": 1,
            "pool": "practice",
            "difficulty": "easy",
            "subtopic_id": "sql.joins",
            "dialect": "sqlite",
            "min_sqlite_version": "3.35",
            "prompt": "Provide the rows.",
            "visible_fixture": fixtures[0],
            "hidden_fixtures": fixtures[1:],
            "reference_query": "SELECT n FROM t",
            "expected_results": results,
            "compare": {
                "order_sensitive": False,
                "duplicate_sensitive": True,
                "column_names_matter": False,
            },
        }
    )
    save(foundation, "content/questions/test.yaml", questions)
    save(foundation, "content/lessons/test.yaml", lessons)
    save(foundation, "content/misconceptions.yaml", rules)
    return foundation


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
