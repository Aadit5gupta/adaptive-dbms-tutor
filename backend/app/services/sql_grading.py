"""Run approved SQLite exercises in a fresh, restricted subprocess."""

import json
import platform
import sqlite3
import subprocess
import sys
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import BoundedSemaphore
from typing import Literal, TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError

from app.db.models import SQLExerciseVersion
from content.schemas.models import Comparison
from content.sql_results import ResultRows, equivalent

WORKER = Path(__file__).resolve().parents[1] / "sql_worker" / "worker.py"
FIXTURE_LIMIT = 128_000
QUERY_LIMIT = 8_192
WALL_SECONDS = 3.0
WORKER_SLOTS = BoundedSemaphore(2)
WorkerCode = Literal[
    "unsupported_statement",
    "worker_unavailable",
    "query_denied",
    "invalid_query",
    "execution_limit",
    "output_limit",
    "unsupported_result",
]


class WorkerError(BaseModel):
    error: WorkerCode


class Grade(BaseModel):
    correct: bool
    feedback_code: Literal[
        "correct",
        "result_mismatch",
        "unsupported_statement",
        "worker_unavailable",
        "query_denied",
        "invalid_query",
        "execution_limit",
        "output_limit",
        "unsupported_result",
    ]
    checked_fixtures: int


class Fixture(BaseModel):
    path: str
    sha256: str


class FixtureSpec(BaseModel):
    minimum_sqlite_version: str
    fixtures: list[Fixture]


def worker_supported() -> bool:
    # Resource enforcement is enabled only on the tested platform.
    return platform.system() == "Darwin" and platform.machine() == "arm64"


class FixtureTable(BaseModel):
    name: str
    data: ResultRows


FixturePreview = TypeAdapter(list[FixtureTable])
R = TypeVar("R")


def worker_packet(
    cwd: Path,
    query: bytes,
    *,
    worker: Path = WORKER,
    timeout: float = WALL_SECONDS,
    describe: bool = False,
) -> object:
    try:
        process = subprocess.run(
            [sys.executable, "-I", "-S", str(worker), *(["--describe"] if describe else [])],
            input=query,
            capture_output=True,
            cwd=cwd,
            env={},
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return WorkerError(error="execution_limit")
    except OSError:
        return WorkerError(error="worker_unavailable")

    if process.returncode != 0 or len(process.stdout) > 50_000:
        return WorkerError(error="worker_unavailable")
    try:
        response = json.loads(process.stdout)
        if isinstance(response, dict) and "error" in response:
            return WorkerError.model_validate(response)
        return response
    except (ValidationError, ValueError):
        return WorkerError(error="worker_unavailable")


def invoke_worker(
    cwd: Path, query: bytes, *, worker: Path = WORKER, timeout: float = WALL_SECONDS
) -> ResultRows | WorkerError:
    response = worker_packet(cwd, query, worker=worker, timeout=timeout)
    if isinstance(response, WorkerError):
        return response
    try:
        rows = ResultRows.model_validate(response)
        if not all(len(row) == len(rows.columns) for row in rows.rows):
            return WorkerError(error="worker_unavailable")
        return rows
    except (ValidationError, ValueError):
        return WorkerError(error="worker_unavailable")


def with_fixture(root: Path, fixture: Fixture, run: Callable[[Path], R]) -> R | WorkerError:
    if not worker_supported():
        return WorkerError(error="worker_unavailable")
    fixtures_dir = (root / "content/sql_fixtures").resolve()
    fixture_path = (root / fixture.path).resolve()
    if (
        not fixtures_dir.is_relative_to(root.resolve())
        or not fixture_path.is_relative_to(fixtures_dir)
        or fixture_path.suffix != ".sql"
    ):
        return WorkerError(error="worker_unavailable")
    try:
        with fixture_path.open("rb") as file:
            data = file.read(FIXTURE_LIMIT + 1)
        if len(data) > FIXTURE_LIMIT or sha256(data).hexdigest() != fixture.sha256:
            return WorkerError(error="worker_unavailable")
        with TemporaryDirectory(prefix="dbms-sql-") as directory:
            path = Path(directory)
            (path / "fixture.sql").write_bytes(data)
            if not WORKER_SLOTS.acquire(blocking=False):
                return WorkerError(error="worker_unavailable")
            try:
                return run(path)
            finally:
                WORKER_SLOTS.release()
    except OSError:
        return WorkerError(error="worker_unavailable")


def run_fixture(root: Path, fixture: Fixture, query: str) -> ResultRows | WorkerError:
    if len(query.encode("utf-8")) > QUERY_LIMIT or "\0" in query:
        return WorkerError(error="unsupported_statement")
    return with_fixture(root, fixture, lambda cwd: invoke_worker(cwd, query.encode("utf-8")))


def visible_schema(root: Path, version: SQLExerciseVersion) -> list[FixtureTable] | WorkerError:
    spec = FixtureSpec.model_validate_json(version.fixture_spec)
    response = with_fixture(
        root, spec.fixtures[0], lambda cwd: worker_packet(cwd, b"", describe=True)
    )
    if isinstance(response, WorkerError):
        return response
    try:
        return FixturePreview.validate_python(response)
    except ValidationError:
        return WorkerError(error="worker_unavailable")


def run_visible(root: Path, version: SQLExerciseVersion, query: str) -> ResultRows | WorkerError:
    spec = FixtureSpec.model_validate_json(version.fixture_spec)
    if sqlite3.sqlite_version_info < tuple(map(int, spec.minimum_sqlite_version.split("."))):
        return WorkerError(error="worker_unavailable")
    return run_fixture(root, spec.fixtures[0], query)


def grade_sql(root: Path, version: SQLExerciseVersion, query: str) -> Grade:
    spec = FixtureSpec.model_validate_json(version.fixture_spec)
    if sqlite3.sqlite_version_info < tuple(map(int, spec.minimum_sqlite_version.split("."))):
        return Grade(correct=False, feedback_code="worker_unavailable", checked_fixtures=0)
    comparison = Comparison.model_validate_json(version.comparison_spec)
    expected_results = json.loads(version.expected_result_spec)
    for count, fixture in enumerate(spec.fixtures, 1):
        actual = run_fixture(root, fixture, query)
        if isinstance(actual, WorkerError):
            return Grade(correct=False, feedback_code=actual.error, checked_fixtures=count)
        expected = expected_results[fixture.path]
        target = ResultRows.model_validate(
            expected if isinstance(expected, dict) else {"columns": [], "rows": expected}
        )
        if not equivalent(actual, target, comparison):
            return Grade(correct=False, feedback_code="result_mismatch", checked_fixtures=count)
    return Grade(correct=True, feedback_code="correct", checked_fixtures=len(spec.fixtures))
