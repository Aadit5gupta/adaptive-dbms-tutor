"""Standalone bounded evaluator. Its only files are the exercise fixtures."""

import json
import os
import re
import resource
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from time import monotonic

MAX_QUERY_BYTES = 8_192
MAX_RESULT_BYTES = 48_000
MAX_ROWS = 200
SQLITE_HEAP_BYTES = 16 * 1024 * 1024

FUNCTIONS = frozenset(
    [
        "abs",
        "avg",
        "coalesce",
        "count",
        "glob",
        "ifnull",
        "instr",
        "length",
        "like",
        "lower",
        "ltrim",
        "max",
        "min",
        "nullif",
        "replace",
        "round",
        "rtrim",
        "substr",
        "sum",
        "total",
        "trim",
        "typeof",
        "upper",
    ]
)
LEADING_TOKEN = re.compile(r"(?P<skip>\s+|--[^\r\n]*|/\*.*?\*/)|(?P<word>[A-Za-z_0-9]+)", re.DOTALL)


def starts_read_query(query: str) -> bool:
    position = 0
    while token := LEADING_TOKEN.match(query, position):
        if token.lastgroup == "word":
            return token.group().upper() in ("SELECT", "WITH")
        position = token.end()
    return False


class RejectedQuery(ValueError):
    pass


def restrict_process() -> None:
    for limit, requested in (
        (resource.RLIMIT_CPU, 2),
        (resource.RLIMIT_FSIZE, 2 * 1024 * 1024),
        (resource.RLIMIT_NOFILE, 24),
        (resource.RLIMIT_CORE, 0),
    ):
        _, hard = resource.getrlimit(limit)
        cap = min(requested, hard) if hard != resource.RLIM_INFINITY else requested
        resource.setrlimit(limit, (cap, cap))


def fixtures() -> dict[str, set[str]]:
    with closing(sqlite3.connect("fixture.sqlite")) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(Path("fixture.sql").read_text(encoding="utf-8"))
        ordinary = db.execute(
            "SELECT name FROM pragma_table_list WHERE schema = 'main' AND type = 'table'"
            " AND name NOT LIKE 'sqlite_%'"
        )
        tables = {
            name: {
                column[0] for column in db.execute("SELECT name FROM pragma_table_info(?)", (name,))
            }
            for (name,) in ordinary
        }
    os.chmod("fixture.sqlite", 0o400)
    return tables


def evaluate(query: str, tables: dict[str, set[str]]) -> str:
    if len(query.encode("utf-8")) > MAX_QUERY_BYTES or not starts_read_query(query):
        raise RejectedQuery("unsupported_statement")

    with closing(sqlite3.connect("file:fixture.sqlite?mode=ro&immutable=1", uri=True)) as db:
        db.enable_load_extension(False)
        db.execute("PRAGMA trusted_schema = OFF")
        db.execute("PRAGMA query_only = ON")
        cap = db.execute(f"PRAGMA hard_heap_limit = {SQLITE_HEAP_BYTES}").fetchone()
        if cap is None or not 0 < cap[0] <= SQLITE_HEAP_BYTES:
            raise RejectedQuery("worker_unavailable")
        for name, cap in (
            (sqlite3.SQLITE_LIMIT_LENGTH, 64_000),
            (sqlite3.SQLITE_LIMIT_SQL_LENGTH, MAX_QUERY_BYTES),
            (sqlite3.SQLITE_LIMIT_COLUMN, 32),
            (sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 40),
            (sqlite3.SQLITE_LIMIT_COMPOUND_SELECT, 8),
            (sqlite3.SQLITE_LIMIT_FUNCTION_ARG, 16),
            (sqlite3.SQLITE_LIMIT_ATTACHED, 0),
            (sqlite3.SQLITE_LIMIT_VDBE_OP, 12_000),
        ):
            db.setlimit(name, cap)

        def authorize(
            action: int, left: str | None, right: str | None, database: str | None, _: str | None
        ) -> int:
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            # Columnless reads can have no schema name for count(*) and CTEs.
            if (
                action == sqlite3.SQLITE_READ
                and left is not None
                and left in tables
                and (
                    (right == "" and database in (None, "main"))
                    or (database == "main" and right in tables[left])
                )
            ):
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_FUNCTION and right in FUNCTIONS:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        ticks = 0
        deadline = monotonic() + 1.0

        def progress() -> int:
            nonlocal ticks
            ticks += 1
            return int(ticks >= 600 or monotonic() >= deadline)

        db.set_authorizer(authorize)
        db.set_progress_handler(progress, 1_000)
        cursor = db.execute(query)
        columns = [column[0] for column in cursor.description or ()]
        columns_json = json.dumps(columns, ensure_ascii=True)
        rows: list[str] = []
        size = len(columns_json)
        for row in cursor:
            if len(rows) >= MAX_ROWS:
                raise RejectedQuery("output_limit")
            encoded = json.dumps(row, allow_nan=False, ensure_ascii=True)
            size += len(encoded) + 1
            if size > MAX_RESULT_BYTES:
                raise RejectedQuery("output_limit")
            rows.append(encoded)
        return '{"columns":' + columns_json + ',"rows":[' + ",".join(rows) + "]}"


def main() -> None:
    try:
        restrict_process()
        packet = sys.stdin.buffer.read(MAX_QUERY_BYTES + 1)
        if len(packet) > MAX_QUERY_BYTES:
            raise RejectedQuery("unsupported_statement")
        query = packet.decode("utf-8")
        tables = fixtures()
    except RejectedQuery as error:
        print(json.dumps({"error": str(error)}))
        return
    except (OSError, sqlite3.Error, UnicodeError, ValueError):
        print('{"error":"worker_unavailable"}')
        return

    try:
        print(evaluate(query, tables))
    except RejectedQuery as error:
        print(json.dumps({"error": str(error)}))
    except sqlite3.Error as error:
        code = getattr(error, "sqlite_errorcode", -1)
        category = {
            sqlite3.SQLITE_AUTH: "query_denied",
            sqlite3.SQLITE_INTERRUPT: "execution_limit",
            sqlite3.SQLITE_TOOBIG: "output_limit",
            sqlite3.SQLITE_NOMEM: "execution_limit",
        }.get(code, "invalid_query")
        print(json.dumps({"error": category}))
    except (MemoryError, OverflowError):
        print('{"error":"execution_limit"}')
    except (ValueError, TypeError):
        print('{"error":"unsupported_result"}')


if __name__ == "__main__":
    main()
