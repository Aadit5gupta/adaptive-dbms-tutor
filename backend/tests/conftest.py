import json
import shutil
from pathlib import Path

import pytest

from scripts.validate_content import ROOT

from .content_fixtures import APPROVED, mcq, save


@pytest.fixture
def foundation(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "content/curriculum", tmp_path / "content/curriculum")
    shutil.copytree(ROOT / "content/manifests", tmp_path / "content/manifests")
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
        questions.extend(
            mcq(id_, topic, pool=pool, code=code)
            for id_, pool in zip(detectors, ("diagnostic", "practice"), strict=True)
        )
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
