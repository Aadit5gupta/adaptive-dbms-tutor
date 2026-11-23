# DBMS Mentor — implementation status

**Authority:** `MASTER_PLAN.md` v1.2. This is a factual report; initial statuses below are NOT claims of tested code.

- **Current stage:** S0
- **Passing commits:** use `git log --oneline --grep='^S[0-6]\.'` (a commit cannot embed its own hash)
- **Last updated by implementation agent:** 2026-11-23
- **Environment/OS/tested versions:** see bootstrap CLI checks in `DECISIONS.md`
- **Default scope:** lean MVP until real deadline/review capacity confirmed in `DECISIONS.md`

## Content (derive counts from validator output, never estimate)

| Measure | Current confirmed | S1 exit | Lean MVP S4 exit |
|---|---:|---:|---:|
| Human-reviewed MCQs (`author_verified` or better) | 0 | ≥12 including ≥4 ordinary practice | ≥30 |
| Complete enabled misconception definitions | 0 | ≥2 | ≥3 |
| Human-reviewed lessons | 0 | ≥2 | ≥6 |
| SQL exercises with independently checked expected results on all fixtures | 0 | ≥1 | ≥6 |
| Indexed books in searchable FTS (not just licensed) | 0 | 0 acceptable (authored lesson fallback) | target 2; report actual count |
| Five catalog entries | 5 | 5 | 5 |

**Important:** the structural `--strict` check can pass with zero enabled misconceptions; the **S1 stage gate** must explicitly fail until its content minima pass. Unreviewed AI-drafted content never counts.

## S0 — Source of truth, content schema, bootstrap

| Task | Status | Actual tests/commands/results | Date/commit |
|---|---|---|---|
| S0.1 canonical docs and Git setup | done_tested | Verified 4 relative links, canonical paths, Git ignore examples and SQLite FTS5/BM25 probe. Files: plan, decisions, status, stage checklist, README, Git ignore and example env. Pushed to private `origin/main` over HTTPS. | 2026-11-23 / `7509d1c` |
| S0.2 content schema + strict structural/stage validator | done_tested | Added `content/schemas`, curriculum YAML, `scripts/validate_content.py`, backend dev dependencies and validator tests. Pytest 15 passed; Ruff and strict mypy passed; strict CLI passed; real S1 gate exited 1 with zero reviewed items as expected. Synthetic S1 test passes. Pushed to `origin/main`. | 2026-11-23 / `533309d` |
| S0.3 dated books manifest + clearance validation | done_tested | Added rights models, exact UTF-8 hash and approval checks, content clearance references, contributor docs and tests. Pytest 24 passed; Ruff, strict mypy and strict content CLI passed (5 catalog entries, 0 approved sections). Search index and atomic import verification follow in S3. Pushed to `origin/main`. | 2026-11-23 / `1b38a0e` |
| S0.4 FastAPI/SQLite skeleton, `/api/v1/health` | done_tested | Added application settings, SQLite FK enforcement, Alembic baseline, readiness router, API tests and README commands. Pytest 27 passed; Ruff, strict mypy and strict content CLI passed. Alembic upgrade/current reported `0001_baseline (head)`. Pushed to `origin/main`. | 2026-11-23 / `4f4acd2` |
| S0.5 React shell + local API proxy + tests | done_tested | Added Vite/React/Tailwind shell, router, readiness states, frontend lockfile, tests and README. Vitest 2 passed; frontend lint/typecheck/build passed. Live loopback Vite /learn and proxied FastAPI health succeeded. Backend 27 tests, Ruff and strict mypy passed. Pushed to `origin/main`. | 2026-11-23 / `7ef90b1` |
| S0.6 CI and source/secret hygiene | done_tested | Added GitHub Actions checks, backend lockfile, shared check script, test report and locked README setup. Clean locked backend setup and npm ci succeeded; 27 backend and 2 frontend tests passed; lint, types, build, content and fresh migration passed. GitHub Actions run pending push. | 2026-11-23 / `S0.6` |
| S0.7 initial draft content for human verification | todo | | |
| **S0 exit** | todo | | |

## S1 — Complete walking skeleton in browser

| Task | Status | Actual tests/commands/results | Date/commit |
|---|---|---|---|
| S1.1 versioned migrations and dedicated demo identities | todo | | |
| S1.2 question allocation, answer withholding, deterministic grader | todo | | |
| S1.3 mastery + independent evidence boundary tests | todo | | |
| S1.4 definition/learner misconception states + checkpoints | todo | | |
| S1.5 SQL sandbox + hidden-fixture result grading | todo | | |
| S1.6 atomic, idempotent attempt and minimal explainable policy | todo | | |
| S1.7 minimal browser learning loop and protected seeded demo CLI | todo | | |
| S1.8 content human review + `--stage S1` + E2E exit | todo | | |
| **S1 exit** | todo | | |

## Later stages

| Stage | Status | Required outcome | Evidence |
|---|---|---|---|
| S2 adaptation/practice | todo | stable sessions, smarter selection and review | |
| S3 rights-cleared retrieval/tutor | todo | approved-lesson and cleared-section BM25 retrieval, actual indexed count and cited fallback | |
| S4 usable auth/product/privacy | todo | multi-user, SQL Lab, diagnostic, export/delete, ≥lean content | |
| S5 mandatory Ollama / hardening / evaluation | todo | Qwen3 grounded tutoring, mock-provider tests, real-model check, security tests and honest evaluation | |
| S6 final docs/demo/viva | todo | fresh-clone reproducible offline demonstration | |

**Allowed task statuses:** `todo | in_progress | done_tested | blocked`. Mark `done_tested` only with executed commands, observed results and date. A passing stage is never inferred from completed scaffolding. If human review/licensing blocks a gate, label it **blocked**, continue eligible engineering work and disclose limitations honestly.
