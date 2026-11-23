# DBMS Mentor — implementation status

**Authority:** `MASTER_PLAN.md` v1.2. This is a factual report; initial statuses below are NOT claims of tested code.

- **Current stage:** S5 engineering (reviewed content and book clearance pending)
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
| S0.6 CI and source/secret hygiene | done_tested | Added GitHub Actions checks, backend lockfile, shared check script, test report and locked README setup. Clean locked backend setup and npm ci succeeded; 27 backend and 2 frontend tests passed; lint, types, build, content and fresh migration passed. GitHub initially rejected the workflow. Pushed after CLI scope refresh. Hosted run pending. | 2026-11-23 / `35b9e78` |
| S0.7 initial draft content for human verification | done_tested | Added 12 draft MCQs, 2 remediation lessons and 2 disabled definitions; added a draft SQL exercise, 3 fixtures and expected result files. Strict validation executed the reference SQL across all fixtures and passed. S1 gate expectedly exited 1. Backend 27 and frontend 2 tests, Ruff, mypy, frontend lint/typecheck/build and migration passed. Initially rejected for missing workflow scope, then pushed to `origin/main`. | 2026-11-23 / `b53178e` |
| **S0 exit** | done_tested | Locked setup, live loopback smoke, full local tests, migration and structural validator passed. Hosted checks were initially pending. Queued commits are now pushed. | 2026-11-23 / `b53178e` |

## S1 — Complete walking skeleton in browser

| Task | Status | Actual tests/commands/results | Date/commit |
|---|---|---|---|
| S1.1 versioned migrations and dedicated demo identities | done_tested | Added ORM models, `0002_learning`, demo identity guard, persistence tests and API notes. Pytest 31 passed, Ruff/mypy/strict validator passed, Alembic upgrade/check/current passed. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `1e3df90` |
| S1.2 question allocation, answer withholding, deterministic grader | done_tested | Added approved-content publisher, assessment DTOs, version-locked MCQ allocation and deterministic idempotent submission service. Pytest 36 passed, Ruff/mypy/strict content validator passed. Browser/API routing follows in S1.7. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `df69e34` |
| S1.3 mastery + independent evidence boundary tests | done_tested | Added pure mastery/confidence and UTC review timing plus boundary, independence and held-out tests. Pytest 47 passed, Ruff/mypy/strict content validation passed. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `e2c3a97` |
| S1.4 definition/learner misconception states + checkpoints | done_tested | Added misconception signal/evidence service and atomic MCQ integration. Pytest 51 passed, including separation of learner evidence and unseen checkpoint transitions. Ruff/mypy/strict content validator passed. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `5237472` |
| S1.5 SQL sandbox + hidden-fixture result grading | done_tested | Added standalone restricted worker, fixture hashes, deterministic result comparator, preview/grader and failure-path tests. Pytest 75 passed; Ruff/mypy/strict content validation passed. Enabled on Apple Silicon macOS; OS address-space limit unavailable, SQLite heap and tested CPU/file/FD limits used. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `8d193e9` |
| S1.6 atomic, idempotent attempt and minimal explainable policy | done_tested | Unified MCQ/SQL submission and persisted mastery, evidence and recommendation in one transaction. Added policy and concurrency/rollback/worker-order tests. Pytest 81 passed; Ruff, mypy and strict content validation passed. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `8719ebf` |
| S1.7 minimal browser learning loop and protected seeded demo CLI | done_tested | Added loopback demo API, React demo page, protected scripts, safety tests and Playwright. 84 backend and 2 frontend tests passed; Ruff, mypy, lint, typecheck, build and 2 real Chrome E2E tests passed with temporary synthetic content. Actual reset and seed succeeded; verified-content replay blocked. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `d4bd841` |
| S1.8 content human review + `--stage S1` + E2E exit | blocked | Drafts are files under `content/`. Owner review and independent SQL result confirmation pending. | 2026-11-23 |
| **S1 exit** | blocked | Engineering completed with synthetic Chrome E2E and SQL tests. Actual reviewed content gate and demo replay exit 1 until human review. | 2026-11-23 |

## Later stages

| Stage | Status | Required outcome | Evidence |
|---|---|---|---|
| S2 adaptation/practice | blocked | stable sessions, smarter selection and review | Engineering tested using synthetic fixtures. Reviewed demo replay still requires content approval. |
| S3 rights-cleared retrieval/tutor | blocked | approved-lesson and cleared-section BM25 retrieval, actual indexed count and cited fallback | Engineering verified. 0 of 5 indexed, and the two-book goal awaits human clearance. |
| S4 usable auth/product/privacy | blocked | multi-user, SQL Lab, diagnostic, export/delete, ≥lean content | Engineering and browser tests passed. All authored content is awaiting human verification. |
| S5 mandatory Ollama / hardening / evaluation | in_progress | Qwen3 grounded tutoring, mock-provider tests, real-model check, security tests and honest evaluation | |
| S6 final docs/demo/viva | todo | fresh-clone reproducible offline demonstration | |

### S2 iterations

| Task | Status | Tests and push | Date/commit |
|---|---|---|---|
| S2.1 Resumable practice and diagnostic allocation | done_tested | Added study service, exposure ordering, domain balancing and tests. Pytest 86 passed, including synthetic replay. Ruff, mypy and strict validation passed. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `9b82a82` |
| S2.2 Recommendation and review | done_tested | Policy v2 recommends actual available difficulty, due topics with fresh questions and explicit repeated practice. Pure policy tests and full backend suite 88 passed; Ruff, mypy and strict validation passed. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `e6e2ecf` |
| S2.3 Progress data and boundary tests | done_tested | Added progress/coverage and recent-accuracy read models, with a privacy and learner-isolation test. Backend 89, Vitest 2 and Chrome E2E 2 passed; lint, types, build and strict validation passed. Actual demo replay exits 1 pending review. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `c00e8d3` |

### S3 iterations

| Task | Status | Tests and push | Date/commit |
|---|---|---|---|
| S3.1 Approved passage import and FTS5 migration | done_tested | Added FTS migration, reviewed lesson indexing, exact-byte book importer, seed integration and tests. Pytest 92 passed; Ruff, mypy, structural validator, Alembic check, actual lesson import and demo seed passed. Actual corpus has zero reviewed or cleared passages. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `e61f6b7` |
| S3.2 BM25 retrieval and source catalog API | done_tested | Added BM25 retrieval, current-rights filtering, FTS vocabulary-derived counts, API and Library screen. Pytest 94, Vitest 2 and Chrome E2E 3 passed; lint, types, build, strict content validator and Alembic check passed. Actual UI reports 0 of 5 indexed. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `15116b1` |
| S3.3 Curated tutor and provider contract | done_tested | Added curated and mock provider contract, citation validation, offline fallback, tutor API and demo form. Pytest 95, Vitest 2, Chrome E2E 3 passed; lint, types, build and strict validation passed. Actual passage corpus awaits review and clearance. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `93fe341` |

### S4 iterations

| Task | Status | Tests and push | Date/commit |
|---|---|---|---|
| S4.1 Local accounts and privacy | done_tested | Added account model/migration, Argon2, hashed sessions, origin and body-error protection, profiles, export and delete. Pytest 99 passed, including origin, redaction, expiry and isolation checks. Ruff, mypy, strict validation and Alembic check passed. Pushed to `origin/main` after workflow authorization. | 2026-11-23 / `f284d1f` |
| S4.2 Signed-in learning and SQL API | done_tested | Added guarded curriculum, lessons, diagnostic, practice, checkpoints, progress, hypothesis, SQL and tutor endpoints. Pytest 100 passed, including cross-account isolation and complete learning-data deletion. Ruff/mypy/strict validation, frontend checks and three Chrome E2E tests passed. Pushed to `origin/main`. | 2026-11-23 / `e74e167` |
| S4.3 Dashboard, learning, SQL Lab and settings UI | done_tested | Added responsive dashboard, learning, practice, progress, Markdown lessons, CodeMirror SQL with visible samples, tutor and privacy settings. Pytest 101, Vitest 2, Chrome E2E 4 passed; lint, types and build passed. Reviewed content remains gated. Pushed to `origin/main`. | 2026-11-23 / `cb333be` |
| S4.4 Lean content drafts and boundary | done_tested | Added original draft keys, SQL and normalization content and grade fixtures. Totals: 30 draft MCQs, 6 draft lessons, 6 draft SQL exercises and 3 disabled patterns. Backend 102, Vitest 2 and Chrome E2E 4 passed; lint, types, build, strict validation, migration check and all SQL reference fixtures passed. Actual S4 content gate exited 1 pending review. Pushed to `origin/main`. | 2026-11-23 / `c0827e5` |

### S5 iterations

| Task | Status | Tests and push | Date/commit |
|---|---|---|---|
| S5.1 Bounded Ollama provider and real-model smoke | done_tested | Added local Ollama adapter, settings, mock HTTP tests, fallback and smoke CLI. Pytest 111 passed with Ruff/mypy/strict validation. Real `qwen3:1.7b` returned a correct cited LEFT JOIN explanation using test-only evidence. Reviewed-corpus check exited 1 awaiting approved passages. Pushed to `origin/main`. | 2026-11-23 / `ab871f8` |
| S5.2 Private follow-ups, progressive hints and SQL context | done_tested | Added conversation migration, owned threads, contextual tutoring, progressive hint eligibility, safe SQL feedback, user export/delete and chat interface. Pytest 113, Vitest 2, Chrome E2E 4 passed, plus Ruff, mypy, content, migration, lint, typecheck and build. | 2026-11-23 / `S5.2` |
| S5.3 Evaluation, privacy hardening and boundary verification | todo | | |

**Allowed task statuses:** `todo | in_progress | done_tested | blocked`. Mark `done_tested` only with executed commands, observed results and date. A passing stage is never inferred from completed scaffolding. If human review/licensing blocks a gate, label it **blocked**, continue eligible engineering work and disclose limitations honestly.
