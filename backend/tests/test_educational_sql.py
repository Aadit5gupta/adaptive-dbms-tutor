"""Independently derive expected rows for the original six SQLite exercises."""

import json
import sqlite3
from collections import Counter
from contextlib import closing

import pytest
from app.db.models import SQLExerciseVersion
from app.services.curriculum import sql_snapshot
from app.services.sql_grading import grade_sql, worker_supported

from content.schemas.models import SQLQuestion
from content.sql_results import Cell
from scripts.validate_content import ROOT, load_content

ALTERNATIVES = {
    "sql_join_001": (
        "SELECT c.id, c.name, (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) "
        "FROM customers c"
    ),
    "sql_sorted_customers": "SELECT id AS customer_key, name FROM customers ORDER BY 1 DESC",
    "sql_matched_customers": (
        "SELECT DISTINCT c.id, c.name FROM customers c JOIN orders o ON o.customer_id = c.id"
    ),
    "sql_unassigned_orders": "SELECT id FROM orders WHERE NOT (customer_id IS NOT NULL)",
    "sql_customers_without_orders": (
        "SELECT c.id, c.name FROM customers c "
        "WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)"
    ),
    "sql_repeat_customers": (
        "SELECT c.id, COUNT(o.id) FROM customers c JOIN orders o ON o.customer_id = c.id "
        "GROUP BY c.id HAVING COUNT(o.id) > 1"
    ),
}

INCORRECT = [
    (
        "sql_join_001",
        "SELECT c.id, c.name, COUNT(*) FROM customers c LEFT JOIN orders o ON o.customer_id=c.id GROUP BY c.id",
    ),
    ("sql_sorted_customers", "SELECT id, name FROM customers ORDER BY id ASC"),
    (
        "sql_matched_customers",
        "SELECT c.id, c.name FROM customers c JOIN orders o ON o.customer_id=c.id",
    ),
    ("sql_unassigned_orders", "SELECT id FROM orders WHERE customer_id = NULL"),
    (
        "sql_customers_without_orders",
        "SELECT id, name FROM customers WHERE id NOT IN (SELECT customer_id FROM orders)",
    ),
    (
        "sql_repeat_customers",
        "SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id HAVING COUNT(*) >= 2",
    ),
    (
        "sql_repeat_customers",
        "SELECT customer_id, 2 FROM orders WHERE customer_id IS NOT NULL GROUP BY customer_id HAVING COUNT(*) >= 2",
    ),
    (
        "sql_repeat_customers",
        "SELECT customer_id, COUNT(*) FROM orders WHERE customer_id IS NOT NULL GROUP BY customer_id HAVING COUNT(*) >= 2 LIMIT 1",
    ),
]


@pytest.fixture(scope="module")
def exercises() -> dict[str, SQLQuestion]:
    return {
        task.id: task
        for task in load_content().questions.values()
        if isinstance(task, SQLQuestion) and task.id in ALTERNATIVES
    }


def oracle(db: sqlite3.Connection) -> dict[str, list[tuple[Cell, ...]]]:
    customers = list(db.execute("SELECT id, name FROM customers"))
    orders = list(db.execute("SELECT id, customer_id FROM orders"))
    counts = Counter(customer for _, customer in orders if customer is not None)
    return {
        "sql_join_001": [(id_, name, counts[id_]) for id_, name in customers],
        "sql_sorted_customers": sorted(customers, reverse=True),
        "sql_matched_customers": [(id_, name) for id_, name in customers if counts[id_]],
        "sql_unassigned_orders": [(id_,) for id_, customer in orders if customer is None],
        "sql_customers_without_orders": [(id_, name) for id_, name in customers if not counts[id_]],
        "sql_repeat_customers": [(id_, counts[id_]) for id_, _ in customers if counts[id_] >= 2],
    }


@pytest.mark.parametrize("exercise_id", ALTERNATIVES)
def test_expected_rows_and_selects_match_independent_oracle(
    exercise_id: str, exercises: dict[str, SQLQuestion]
) -> None:
    task = exercises[exercise_id]
    for result in task.expected_results:
        with closing(sqlite3.connect(":memory:")) as db:
            db.executescript((ROOT / result.fixture).read_text())
            expected_rows = oracle(db)[exercise_id]
            stored = json.loads((ROOT / result.expected_result_file).read_text())
            if isinstance(stored, dict):
                stored = stored["rows"]
            rows = list(map(tuple, stored))
            if task.compare.order_sensitive:
                assert rows == expected_rows, (exercise_id, result.fixture)
            else:
                assert Counter(rows) == Counter(expected_rows), (exercise_id, result.fixture)
            for query in (task.reference_query, ALTERNATIVES[exercise_id]):
                rows = db.execute(query).fetchall()
                if task.compare.order_sensitive:
                    assert rows == expected_rows, (exercise_id, result.fixture, query)
                else:
                    assert Counter(rows) == Counter(expected_rows), (
                        exercise_id,
                        result.fixture,
                        query,
                    )


@pytest.mark.skipif(
    not worker_supported(), reason="restricted SQL worker is Apple Silicon macOS only"
)
def test_restricted_worker_accepts_alternatives_and_rejects_common_mistakes(
    exercises: dict[str, SQLQuestion],
) -> None:
    for id_, query in [*ALTERNATIVES.items(), *INCORRECT]:
        task = exercises[id_]
        fixtures, results = sql_snapshot(ROOT, task)
        variant = SQLExerciseVersion(
            fixture_spec=fixtures,
            expected_result_spec=results,
            dialect=task.dialect,
            reference_query=task.reference_query,
            comparison_spec=task.compare.model_dump_json(),
        )
        outcome = grade_sql(ROOT, variant, query)
        if query == ALTERNATIVES[id_]:
            assert outcome.correct and outcome.checked_fixtures == len(task.fixtures), id_
        else:
            assert outcome.feedback_code == "result_mismatch", (id_, query, outcome)
