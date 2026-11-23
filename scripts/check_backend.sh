#!/usr/bin/env bash
set -euo pipefail

bin=${1:-backend/.venv/bin}
"$bin/python" -m pytest -c backend/pyproject.toml
"$bin/ruff" check --config backend/pyproject.toml backend content scripts
MYPYPATH=backend "$bin/mypy" --config-file backend/pyproject.toml   backend/app backend/tests content scripts
"$bin/python" scripts/validate_content.py --strict
