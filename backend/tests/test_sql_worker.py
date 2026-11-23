import os
import sqlite3
from hashlib import sha256
from pathlib import Path

import pytest
from app.db.models import SQLExerciseVersion
from app.services.curriculum import sql_snapshot
from app.services.sql_grading import (
    Fixture,
    WorkerError,
    grade_sql,
    invoke_worker,
    run_fixture,
    run_visible,
    worker_supported,
)

from content.schemas.models import SQLQuestion
from content.sql_results import ResultRows
from scripts.validate_content import ROOT, load_content

TESTED_PLATFORM = pytest.mark.skipif(
    not worker_supported(), reason="SQL worker is disabled on this platform"
)


@pytest.fixture
def join_exercise() -> SQLExerciseVersion:
    draft = load_content().questions["sql_join_001@1"]
    assert isinstance(draft, SQLQuestion)
    spec, expected = sql_snapshot(ROOT, draft)
    return SQLExerciseVersion(
        question_version_id=draft.ref,
        dialect="sqlite",
        fixture_spec=spec,
        expected_result_spec=expected,
        reference_query=draft.reference_query,
        comparison_spec=draft.compare.model_dump_json(),
    )


@TESTED_PLATFORM
def test_reference_and_equivalent_form_pass_hidden_fixtures(
    join_exercise: SQLExerciseVersion,
) -> None:
    visible = run_visible(ROOT, join_exercise, join_exercise.reference_query)
    assert isinstance(visible, ResultRows)
    assert (2, "Mina", 0) in visible.rows
    equivalent = "SELECT c.id, c.name, (SELECT count(*) FROM orders o WHERE o.customer_id=c.id) FROM customers c"
    assert grade_sql(ROOT, join_exercise, equivalent).checked_fixtures == 3
    assert grade_sql(ROOT, join_exercise, equivalent).correct
    assert grade_sql(ROOT, join_exercise, join_exercise.reference_query).correct
    grade = grade_sql(
        ROOT, join_exercise, join_exercise.reference_query.replace("LEFT JOIN", "JOIN")
    )
    assert not grade.correct and grade.feedback_code == "result_mismatch"


@TESTED_PLATFORM
def test_visible_success_does_not_guarantee_correctness(join_exercise: SQLExerciseVersion) -> None:
    group_by_name = join_exercise.reference_query.replace(
        "GROUP BY c.id, c.name", "GROUP BY c.name"
    )
    grade = grade_sql(ROOT, join_exercise, group_by_name)
    assert not grade.correct
    assert grade.checked_fixtures == 2
    assert grade.feedback_code == "result_mismatch"


@TESTED_PLATFORM
@pytest.mark.parametrize(
    "query",
    [
        "UPDATE customers SET name = 'Synthetic'",
        "DELETE FROM customers",
        "INSERT INTO customers VALUES (7, 'Synthetic')",
        "DROP TABLE customers",
        "ATTACH DATABASE 'other.sqlite' AS other",
        "PRAGMA user_version",
        "SELECT id FROM customers; SELECT 1",
        "SELECT name FROM sqlite_schema",
        "SELECT * FROM pragma_table_list",
        "SELECT zeroblob(12)",
        "SELECT randomblob(12)",
        "SELECT load_extension('unused')",
        "-- explanation\nDELETE FROM customers",
        "WITH clean AS (SELECT 1) DELETE FROM customers",
        "WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM n WHERE i < 3) SELECT i FROM n",
        "SELECT (",
        " " * 8_194,
    ],
)
def test_disallowed_input_returns_safe_error(
    join_exercise: SQLExerciseVersion, query: str, tmp_path: Path
) -> None:
    regular = tmp_path / "app.sqlite"
    with sqlite3.connect(regular) as app:
        app.execute("CREATE TABLE sensitive(private_value TEXT)")
        app.execute("INSERT INTO sensitive VALUES ('Synthetic')")
    before = sha256(regular.read_bytes()).digest()
    assert isinstance(run_visible(ROOT, join_exercise, query), WorkerError)
    assert sha256(regular.read_bytes()).digest() == before


@TESTED_PLATFORM
def test_output_cap_and_query_budget(tmp_path: Path) -> None:
    directory = tmp_path / "content/sql_fixtures"
    directory.mkdir(parents=True)
    content = (
        "CREATE TABLE n(i INTEGER); INSERT INTO n VALUES "
        + ",".join(f"({i})" for i in range(220))
        + ";"
    )
    path = directory / "test.sql"
    path.write_text(content, encoding="utf-8")
    fixture = Fixture(
        path=str(path.relative_to(tmp_path)), sha256=sha256(content.encode()).hexdigest()
    )
    output = run_fixture(tmp_path, fixture, "SELECT i FROM n")
    assert isinstance(output, WorkerError) and output.error == "output_limit"
    limited = run_fixture(
        tmp_path, fixture, "SELECT COUNT(*) FROM n a CROSS JOIN n b CROSS JOIN n c"
    )
    assert isinstance(limited, WorkerError) and limited.error == "execution_limit"


@TESTED_PLATFORM
def test_with_select_and_trusted_fixture_hash(
    join_exercise: SQLExerciseVersion, tmp_path: Path
) -> None:
    result = run_visible(
        ROOT,
        join_exercise,
        "/* example */ WITH data AS (SELECT id FROM customers) SELECT * FROM data",
    )
    assert isinstance(result, ResultRows)
    assert result.rows == [(1,), (2,), (3,)]
    fixture = Fixture(path="content/sql_fixtures/shop_visible.sql", sha256="0" * 64)
    assert run_fixture(ROOT, fixture, "SELECT id FROM customers") == WorkerError(
        error="worker_unavailable"
    )
    assert run_fixture(tmp_path, fixture, "SELECT id FROM customers") == WorkerError(
        error="worker_unavailable"
    )


@TESTED_PLATFORM
def test_process_timeout_reaps_child(tmp_path: Path) -> None:
    program = tmp_path / "wait.py"
    program.write_text(
        "import os, time\nfrom pathlib import Path\n"
        "Path('worker.pid').write_text(str(os.getpid()))\ntime.sleep(10)\n"
    )
    result = invoke_worker(tmp_path, b"", worker=program, timeout=0.5)
    assert isinstance(result, WorkerError) and result.error == "execution_limit"
    pid = int((tmp_path / "worker.pid").read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_unsupported_platform_disables_worker(
    join_exercise: SQLExerciseVersion, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.services.sql_grading.worker_supported", lambda: False)
    assert run_visible(ROOT, join_exercise, "SELECT 1") == WorkerError(error="worker_unavailable")


@TESTED_PLATFORM
def test_os_worker_resource_caps_are_active(tmp_path: Path) -> None:
    from app.services.sql_grading import WORKER

    program = tmp_path / "limits.py"
    program.write_text(
        "import json, resource, runpy\n"
        f"runpy.run_path({str(WORKER)!r})['restrict_process']()\n"
        "limits = [resource.RLIMIT_CPU, resource.RLIMIT_FSIZE, resource.RLIMIT_NOFILE, resource.RLIMIT_CORE]\n"
        "print(json.dumps({'columns': ['value'], 'rows': [[resource.getrlimit(id_)[0]] for id_ in limits]}))\n"
    )
    limits = invoke_worker(tmp_path, b"", worker=program)
    assert isinstance(limits, ResultRows)
    assert limits.rows == [(2,), (2 * 1024 * 1024,), (24,), (0,)]
