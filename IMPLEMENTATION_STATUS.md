# DBMS Mentor — implementation status

**Authority:** `MASTER_PLAN.md` v1.2. This is a factual report; initial statuses below are NOT claims of tested code.

- **Current stage:** Final acceptance audit complete. Conditional go for a local college demo. Public deployment and human-study use remain no-go.
- **Passing commits:** use `git log --oneline --grep='^S[0-6]\.'` (a commit cannot embed its own hash)
- **Last updated by implementation agent:** 2026-11-25
- **Environment/OS/tested versions:** see bootstrap CLI checks in `DECISIONS.md`
- **Default scope:** lean MVP until real deadline/review capacity confirmed in `DECISIONS.md`

## Content (derive counts from validator output, never estimate)

| Measure | Learner policy | AI-verified | Human-reviewed | S1 minimum | S4 minimum |
|---|---:|---:|---:|---:|---:|
| MCQs | 46 | 46 | 0 | 12 | 30 |
| Ordinary practice MCQs | 33 | 33 | 0 | 4 | 4 |
| Lessons | 22 | 22 | 0 | 2 | 6 |
| SQL exercises independently checked across all fixtures | 6 | 6 | 0 | 1 | 6 |
| Enabled misconception definitions with full coverage | 3 | 3 | 0 | 2 | 3 |

All 24 Learn topics have material. Twenty-two original lessons are searchable in both local databases. The Library reports **4 of 5 books indexed**, with one licensed text excerpt each from Runestone, BCcampus, Shea and DataField. Both local databases have all four excerpts. S1 and S4 pass with `--review-policy learner`. Both default human-only gates exit 1 with zero qualifying records.

## S0 — Source of truth, content schema, bootstrap

| Task | Status | Actual tests/commands/results | Date/commit |
|---|---|---|---|
| S0.1 canonical docs and Git setup | done_tested | Verified 4 relative links, canonical paths, Git ignore examples and SQLite FTS5/BM25 probe. Files: plan, decisions, status, stage checklist, README, Git ignore and example env. Pushed to private `origin/main` over HTTPS. | 2026-11-23 / `7509d1c` |
| S0.2 content schema + strict structural/stage validator | done_tested | Added `content/schemas`, curriculum YAML, `scripts/validate_content.py`, backend dev dependencies and validator tests. Pytest 15 passed; Ruff and strict mypy passed; strict CLI passed; real S1 gate exited 1 with zero reviewed items as expected. Synthetic S1 test passes. Pushed to `origin/main`. | 2026-11-23 / `533309d` |
| S0.3 dated books manifest + clearance validation | done_tested | Added rights models, exact UTF-8 hash and approval checks, content clearance references, contributor docs and tests. Pytest 24 passed; Ruff, strict mypy and strict content CLI passed (5 catalog entries, 0 approved sections). Search index and atomic import verification follow in S3. Pushed to `origin/main`. | 2026-11-23 / `1b38a0e` |
| S0.4 FastAPI/SQLite skeleton, `/api/v1/health` | done_tested | Added application settings, SQLite FK enforcement, Alembic baseline, readiness router, API tests and README commands. Pytest 27 passed; Ruff, strict mypy and strict content CLI passed. Alembic upgrade/current reported `0001_baseline (head)`. Pushed to `origin/main`. | 2026-11-23 / `4f4acd2` |
| S0.5 React shell + local API proxy + tests | done_tested | Added Vite/React/Tailwind shell, router, readiness states, frontend lockfile, tests and README. Vitest 2 passed; frontend lint/typecheck/build passed. Live loopback Vite /learn and proxied FastAPI health succeeded. Backend 27 tests, Ruff and strict mypy passed. Pushed to `origin/main`. | 2026-11-23 / `7ef90b1` |
| S0.6 CI and source/secret hygiene | done_tested | Added GitHub Actions checks, backend lockfile, shared check script, test report and locked README setup. Clean locked backend setup and npm ci succeeded; 27 backend and 2 frontend tests passed; lint, types, build, content and fresh migration passed. GitHub initially rejected the workflow. Pushed after CLI scope refresh. Hosted CI verified. | 2026-11-23 / `35b9e78` |
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
| S5 mandatory Ollama / hardening / evaluation | blocked | Qwen3 grounded tutoring, mock-provider tests, real-model check, security tests and honest evaluation | Real provider verified with test evidence. Reviewed-corpus model check and retrieval metrics await content approval. |
| S6 final docs/demo/viva | blocked | fresh-clone reproducible offline demonstration | Clean GitHub clone setup, full tests and real model transport passed. Real-course demo and corpus acceptance await human review. |

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
| S5.2 Private follow-ups, progressive hints and SQL context | done_tested | Added conversation migration, owned threads, contextual tutoring, progressive hint eligibility, safe SQL feedback, user export/delete and chat interface. Pytest 113, Vitest 2, Chrome E2E 4 passed, plus Ruff, mypy, content, migration, lint, typecheck and build. Pushed and hosted CI passed. | 2026-11-23 / `f30be59` |
| S5.3 Evaluation, privacy hardening and boundary verification | done_tested | Added hit@k/MRR and synthetic policy tools, SQL fixture path guard, no-store headers and safe republishing checks. Pytest 116, Vitest 2, Chrome E2E 4 passed with lint, types, build, content and migration. Real Qwen3 explanation and follow-up passed on 8 GiB. Real-corpus retrieval evaluation remains blocked. Pushed to `origin/main`. | 2026-11-23 / `121669c` |

### S6 iterations

| Task | Status | Tests and push | Date/commit |
|---|---|---|---|
| S6.1 Architecture, schema, demo and viva | done_tested | Added architecture and ER diagrams, schema dictionary, exact demo walkthrough, README updates and pinned the demo's documented JOIN exercise. Pytest 117, Ruff/mypy/content validation and 22 local links passed. Pushed to `origin/main`; CI passed. | 2026-11-23 / `5df42ea` |
| S6.2 Fresh-clone and hosted verification | done_tested | Verified GitHub clone `5df42ea`, fresh dependencies and database, 117 backend tests, 2 Vitest tests and 4 Chrome tests, lint, types, build and real Ollama. Hosted CI passed. Live workspace frontend, API, catalog and demo identities responded. Observed review-gate failures documented. | 2026-11-23 / `S6.2` |
| S6.3 Original learner content verification and activation | done_tested | Verified and published 45 original items using two AI review passes. Updated the content schemas, migration, publication, retrieval attribution, fixtures, review documents and authored Chrome demo. Both learner gates, 130 backend tests, two Vitest tests, five Chrome scenarios, CLI replay, schema checks and real indexed-corpus Ollama passed. Pushed to `origin/main`. [Hosted checks passed](https://github.com/Aadit5gupta/adaptive-dbms-tutor/actions/runs/45167065757). | 2026-11-23 / `2905a27` |
| S6.5 Final acceptance corrections | done_tested | Fixed mixed-session resumption, repeated-detector independence, open-item hints, SQL feedback and error messages, demo Markdown, and mobile lesson overflow. Pytest 138, Vitest 2, Chrome regression 6 and real Chrome acceptance journeys verified. Both learner gates, Alembic, the authored replay, and real Ollama and offline fallback passed. Pushed to `origin/main`. [Hosted checks passed](https://github.com/Aadit5gupta/adaptive-dbms-tutor/actions/runs/45170749595). | 2026-11-23 / `3b56e5c` |
| S6.6 Final acceptance report | done_tested | [Report](docs/FINAL_ACCEPTANCE_REPORT.md) records actual Chrome journeys, fixes, screenshots, remaining defects, and separate readiness decisions. | 2026-11-23 |
| S6.7 Browser demo reset | done_tested | Added a confirmed reset for both synthetic learners. The authenticated learner database remains outside the operation. Pytest 139, Vitest 2, Chrome 6, build, lint, type checks, S4 learner validation and authored CLI replay passed. | 2026-11-23 |
| S6.8 Learn curriculum coverage | done_tested | Added 16 AI-verified original lessons and 16 practice questions in the two `coverage.yaml` files. Published in both local databases. Pytest 139, Vitest 2, Chrome 7, lint, type checks, build, learner S1/S4 gates and authored CLI replay passed. All 16 new lessons were retrieved from FTS5 in both databases. Real Ollama grounded its reply in a new lesson. See [test report](docs/test-report.md#learn-coverage-25-november-2026). | 2026-11-25 |
| S6.9 Publisher-licensed textbook excerpts | done_tested | Bundled two publisher-license-verified excerpts. Added scoped rights validation, hash checks, repeatable imports and visible license links. Both local databases indexed 24 passages. Pytest 145, Vitest 2, Chrome 7, S1/S4 learner gates, authored CLI replay and real Ollama passed. | 2026-11-25 |
| S6.10 Additional licensed textbook sources | done_tested | Added Shea Chapter 8 for noncommercial use and DataField Chapter 26 under its published CC BY-SA license. Both local databases index 26 passages. Pytest 145, Vitest 2, Chrome 7, learner gates and authored replay passed. Real Ollama cited both new excerpts. | 2026-11-25 |
| S6.11 Library and Tutor navigation | done_tested | Search filters apply before ranking, FTS5 previews show matching text, and sources link to the appropriate lesson or chapter. Added a topic-specific Tutor link with an editable draft. Pytest 146, Vitest 2, Chrome 8, lint, type checks, build, S4 learner gate, authored replay and real Ollama textbook citation passed. | 2026-11-25 |
| S6.12 One-click practice hints and optional specific clues | done_tested | The first click shows a prepared hint, and later clicks show the next levels. Optional typed questions select safe reasoning prompts by supported topic and keywords. Added regression coverage for empty hint input, targeted fallback, no model calls, hint order and mobile question transitions. Pytest 146, Vitest 2, Chrome 9, lint, type checks, build and S4 learner gate passed. | 2026-11-25 |
| S6.13 Preserve normalization examples in tutor explanations | done_tested | Preserved both examples within the existing Ollama prompt budget. Added a source-backed curated explanation for the reproduced comparison. Pytest 148, Vitest 2, Chrome 9, lint, types, build, strict validation, authored replay, and real Ollama lesson/book checks passed. | 2026-11-25 |
| S6.14 Signed-in misconception feedback | done_tested | A graded answer that updates evidence now shows the authoritative status and signal count. Progress has a named Misconceptions section, an empty state, and a remediation link when recommended. Pytest 148, Vitest 2, Chrome 10, lint, type checks, build, S4 learner gate and authored A/B CLI replay passed. | 2026-11-25 |
| S6.15 Practice question transition and diagnostic navigation | done_tested | Fixed the duplicate React keys that left an answered question on screen. Added one submission status and direct topic-diagnostic links from possible misconception feedback and Progress. Verified the exhausted diagnostic message. Pytest 148, Vitest 2, Chrome 10, lint, type checks, build, strict validation and authored demo replay passed. | 2026-11-25 |
| S6.16 Scope and difficulty allocation audit | done_tested | Compared all 52 published versions in both databases. Scoped diagnostics can resume matching items from a previously allocated screening. Topic and difficulty scopes are honored and shortages appear in the UI. Pytest 154, Vitest 2, Chrome 11, Ruff, mypy, frontend lint, types, build and strict content validation passed. Pushed to `origin/main` and Actions passed. | 2026-11-25 / `d745470` |
| S6.17 Independent progression and recommendation audit | done_tested | Added mastery v2 and migration 0008, policy v3, lesson-specific reteaching, precise recommendation routes and learner trajectory regressions. Pytest 162, Vitest 2, Chrome 15, Ruff, mypy, frontend lint/types/build, S1/S4 learner gates, 33 targeted SQL checks, authored A/B replay, migration checks and both real Ollama probes passed. Pushed to `origin/main` and Actions passed. See the [audit](docs/ADAPTIVE_LEARNING_AUDIT.md) for limitations. | 2026-11-25 / `81fcd89` |
| S6.18 Exact SQL recommendation regression | done_tested | Verified that an exhausted JOIN MCQ sequence recommends a specific unattempted SQL exercise, opens that version even with another same-topic exercise open, resumes that selection, and falls back if the SQL worker is unavailable. Full backend suite 163 passed, including 14 progression checks. No runtime code changes. | 2026-11-25 |
| Human review and additional publisher scopes | blocked | Human-only assessment gates and human pilot sign-off require actual human review. Unresolved section exceptions need separate clearance. OpenStax remains link-only pending written permission. | 2026-11-25 |

**Allowed task statuses:** `todo | in_progress | done_tested | blocked`. Mark `done_tested` only with executed commands, observed results and date. A passing stage is never inferred from completed scaffolding. If human review/licensing blocks a gate, label it **blocked**, continue eligible engineering work and disclose limitations honestly.
