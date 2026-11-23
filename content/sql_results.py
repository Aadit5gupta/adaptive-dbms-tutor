"""Deterministic comparison for SQLite result schemas and row multisets."""

from collections import Counter
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, StrictFloat, StrictInt, StrictStr

from content.schemas.models import Comparison

Cell: TypeAlias = StrictStr | StrictInt | StrictFloat | None


class ResultRows(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    columns: list[str]
    rows: list[tuple[Cell, ...]]


def equivalent(actual: ResultRows, expected: ResultRows, policy: Comparison) -> bool:
    if policy.column_names_matter and expected.columns != actual.columns:
        return False
    if expected.columns and len(expected.columns) != len(actual.columns):
        return False
    if not all(len(row) == len(actual.columns) for row in expected.rows):
        return False

    actual_rows, expected_rows = actual.rows, expected.rows
    if not policy.duplicate_sensitive:
        actual_rows = list(dict.fromkeys(actual_rows))
        expected_rows = list(dict.fromkeys(expected_rows))
    if policy.order_sensitive:
        return actual_rows == expected_rows
    return Counter(actual_rows) == Counter(expected_rows)
