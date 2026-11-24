# Codex task checklist — S0 and S1

**Source of truth:** `../MASTER_PLAN.md` v1.2. This is an *execution checklist*, not an alternative design. Follow the canonical enums/ref formats in the master plan and `content_authoring_guide.md`. Each task is small enough for a test-backed commit. Use `S0.1`, `S0.2`, ... for commit subjects. Do not declare S1 complete without an actual browser journey, human-approved content and adversarial SQL tests.

The original engineering sequence below retains historical human gate references. Post-build learner activation uses the explicit learner gate in [the authoring guide](content_authoring_guide.md).

## S0 — Working foundation and content contracts

### S0.1 — Repo and docs integrity

**Files:** `MASTER_PLAN.md`, `AGENTS.md`, `DECISIONS.md`, `IMPLEMENTATION_STATUS.md`, `docs/*.md`, `.gitignore`, `.env.example`, `README.md`.

**Build:** Check whether a project exists; initialize Git only if needed. Record required Ollama tutoring, FTS5/BM25 grounding, low-memory limits and curated fallback in the canonical plan and status. Ensure exactly one active product plan and correct file locations. Keep old plans backed up/versioned rather than silently deleting work. Ignore DB files, tokens, generated/book source text and hidden SQL fixture answers as appropriate.

**Tests:** document navigation links resolve; `git status` is safe; no obsolete plan remains authoritative; no secrets in tracked files. **Accept:** Codex can find all required docs from `AGENTS.md`.

### S0.2 — Canonical content schemas and validator

**Files:** `content/schemas/`, `content/curriculum/topics.yaml`, `scripts/validate_content.py`, `backend/tests/test_validate_content.py`, test-only fixtures.

**Build:** Define 7 curriculum domains + stable subtopic IDs; questions with immutable `id@version` refs, canonical `pool` enum, one correct option, source/review metadata; lessons, SQL tasks, misconception definitions. Define review statuses `draft|ai_verified|author_verified|independent_verified`, definition boolean `enabled`, per-user state separately. Implement `--strict` and `--stage S1`/`--stage S4` CLI validations. Treat `detector` as a **role**, never a question pool. Include prerequisite cycle check and no checkpoint/held-out leakage. Include explicit tests of same ID with two versions vs duplicate identical versions.

**Tests:** every invalid fixture fails with actionable path/message; 0 approved definitions may pass structural strict but must **fail `--stage S1`**; supported complete S1 fixture passes. **Accept:** test-only fixtures do not seed production.

### S0.3 — Rights manifest contracts

**Files:** `content/manifests/books.yaml`, manifest schema/checker, rights tests.

**Build:** Load five catalog entries, license evidence, per-section exceptions. The provided YAML is **not** clearance. A section can be imported only with a valid per-section rights record, recorded reviewer, date and license, and a matching content hash. See the current rights policy in MASTER_PLAN.md §4. BCcampus Chapters **10 and 11** need independent checks; DataField remains link-only. Import-count model derives from committed chunks, not YAML approvals.

**Tests:** missing/duplicate book IDs, unknown statuses, DataField permission violation, uncleared section import, hash mismatch and failed import all rejected. No authoritative `indexed_section_count` in manifest. **Accept:** five catalog records and zero indexed books at bootstrap.

### S0.4 — Backend skeleton

**Files:** `backend/pyproject.toml`, `backend/app/main.py`, config/DB setup, tests, `.env.example`.

**Build:** Python 3.11+ FastAPI, Pydantic v2, SQLite connection with FK enforcement, migrations initialized, `/api/v1/health` reports readiness. Use separate env-configured `data/app.sqlite` and `data/demo.sqlite` and reject equal/resolved matching paths. App binds local host by default.

**Tests:** pytest health response, temporary migration/DB open, Ruff. **Accept:** bootstrap works without an AI provider or hosted DB.

### S0.5 — Frontend shell

**Files:** `frontend/*`, Vite proxy, router, one UI test.

**Build:** React TS Vite Tailwind + TanStack Query; navigable Dashboard/Learn/Practice/SQL Lab/Library/Progress shells, accessible keyboard focus, API health indicator. Placeholder features must clearly say “Not available yet”, not fake clickable actions.

**Tests:** npm lint, TS check, build, basic Vitest component. **Accept:** page loads and health check works via same-origin `/api` proxy.

### S0.6 — CI and repeatability

**Files:** `.github/workflows/ci.yml`, `README.md`, `docs/test-report.md`.

**Build:** Run backend tests/Ruff, strict structural content validator, frontend checks, migrations. `--stage S1` is an exit gate for S1 and must enter normal CI after S1 completes; do not impose unachieved S1 content minimum at S0 bootstrap. Use mock providers for automated AI tests. Keep real-model verification separately invoked and leave all model downloads to the owner. Avoid fetching licensing-restricted sources in CI.

**Tests:** run workflow equivalently locally; report CI result when it actually runs. **Accept:** clean checkout setup documented.

### S0.7 — First authoring drafts, explicit human review

**Files:** `content/questions/`, `content/lessons/`, `content/misconceptions.yaml`, `content/sql_fixtures/`.

**Build:** Codex may create **draft** original questions/lessons for `KEYS-02` and `SQL-JOIN-01`, with ≥2 detector logical questions + 2 checkpoint logical questions per pattern, original remediation lesson and preliminary join exercise fixtures. It must **not** claim these are human reviewed or switch `enabled=true` without owner verification. See authoring guide.

**Tests:** `validate_content.py --strict` validates drafts and reports accurate counts. **S0 exit:** apps start, docs present, content schema and rights manifest valid, drafted content ready for owner review, no invented human approval.

---

## S1 — First genuinely useful end-to-end tutor

### S1.1 — Core versioned persistence and safe demo identities

**Files:** SQLAlchemy models, Alembic migrations, migration tests, demo config.

**Build:** question/lesson version tables; session items tied to version; append-only attempts; mastery and history; misconception definitions/evidence/per-user states; policy decisions/recommendations; synthetic demo users only in dedicated database. UNIQUE `(question_id,version)`, `(lesson_id,version)`, `(user_id,subtopic_id,model_name)`, `(user_id,idempotency_key)`, `(session_item_id)`; enforce FKs.

**Tests:** migration from empty DB, uniqueness, FK rejection, approved content version cannot be mutated, independent demo/app DB check. **Accept:** no anonymous public multi-user API; dev-only demo session context.

### S1.2 — Content loader + deterministic MCQs

**Files:** loader/assessment service, Pydantic DTOs, API/tests.

**Build:** only publication-eligible versions load into production/demo learning pool, server allocates questions, answer withheld, single submit per session item, first grade recorded. Detector role comes from a wrong-option mapping; checkpoint allocation restricted to learner-unseen reserved pool; pre/post pools never exposed as practice.

**Tests:** incorrect vs correct grading, key/distractor leakage, duplicate attempts across sessions, SQL content not parsed as MCQ, two published versions preserve original attempts. **Accept:** no hidden key in pre-submit DTO.

### S1.3 — Pure mastery model and confidence

**Files:** mastery service/tests.

**Build:** baseline score = old + .2*(evidence-old) clipped [0,1], default 0.5. Confidence counts distinct logical question IDs with independent evidence; hinted responses and repeats don't boost confidence. Review scheduling is separate from score.

**Tests:** wrong .5→.4; successive correct .5→.6→.68→.744; boundary <=.4 low vs >.4 medium; score upper/lower bounds; no inflation on replay/question version; held-out no training update. **Accept:** pure deterministic service.

### S1.4 — Conservative misconception hypotheses

**Files:** misconception service, content definition mapper, tests.

**Build:** one independent mapped wrong answer → `possible`; second *distinct logical ID* → `active`; remediation with two distinct unseen, unhinted correct checkpoints → `resolved`; otherwise `improving` or still `active` as justified. Historical evidence append-only. Definition `review_status` and learner `state` never share a field.

**Tests:** two detectors required, same ID new version not independent, wrong unmapped distractor no signal, hint reveal ignored, exhausted checkpoint doesn't auto-resolve, no cross-user evidence leakage.

### S1.5 — Restricted SQL worker and result evaluator

**Files:** subprocess entrypoint, fixtures, SQL grading service, hostile-query tests.

**Build:** SQLite SELECT/WITH SELECT only (parser + SQLite authorizer), bound to a disposable immutable read-only fixture, allowlisted tables/functions, extensions disabled, SQL/query size limits (`setlimit`), progress handler, output/row caps, parent killable wall-clock timeout and tested platform-specific memory/CPU restrictions. Explicitly reject blob bombs and arbitrary PRAGMAs/ATTACH/schema/file access. For Windows, do not enable untrusted worker until equivalent restrictions are implemented/tested. The task's reference query and **separately defined expected output** must match on visible and hidden fixtures; compare equivalent SQL solutions using ordered sequence or unordered multiset per task. `Run` is ungraded; `Submit` is graded.

**Tests:** valid LEFT JOIN and equivalent formulation pass; INNER JOIN dropping unmatched rows fails; duplicates/missing NULLs uncovered; `DROP`, multi-statement, `ATTACH`, `PRAGMA`, `zeroblob`, `randomblob`, recursive CTE and huge join fail safely without app DB changes. Verify timeout really kills child; document only platforms actually tested. **Accept:** no learner query ever touches application database.

### S1.6 — Atomic attempts, decision policy, idempotency

**Files:** service/API/transaction tests.

**Build:** worker SQL grading completed *before* write lock. `BEGIN IMMEDIATE` (or tested equivalent) rechecks session item and payload fingerprint, writes attempt/result, mastery, misconception evidence, policy snapshot and recommendation atomically. Different payload with reused idempotency key → HTTP 409; exact retry returns identical stored result; policy prefers active supported remediation over arbitrary unassessed unrelated topic when material exists, handles prerequisites, fallback and no-content honestly.

**Tests:** concurrent duplicates, repeated attempts, rollback on internal error, persisted reasons, two learners diverge. **Accept:** at most one committed evidence update per allocated item.

### S1.7 — Minimal browser flow + safe deterministic demo

**Files:** simple browser pages/components, `scripts/reset_demo.py`, `seed_demo.py`, `verify_demo.py`, E2E test.

**Build:** lightweight dev-only local demo UI (no elaborate design): A answers two keys misconception detectors, sees targeted lesson and two unseen checkpoints, then updated recommendation; B sees different JOIN remediation, runs/submits real SQL query. Demo data explicitly labeled synthetic. Reset script refuses any path other than the configured allowlisted `data/demo.sqlite` (or ephemeral test path), never touches app DB, and exercises a repeatable reset→seed→verify sequence. No arbitrary client-supplied `user_id` outside dedicated loopback demo context.

**Tests:** successful browser path, after-refresh state, demo reset safety with app DB checksum and real-user test record preserved; no Ollama or network needed. **Accept:** this is visible to a reviewer, not only a backend test.

### S1.8 — Human content sign-off and stage exit

**Files:** verified content metadata, validator test report, `IMPLEMENTATION_STATUS.md`.

**Build:** owner checks sources, answer keys/distractors, original remediation lessons and SQL expected outputs independently. Promote eligible content manually to `author_verified`, flip complete rule `enabled=true`. Require **≥12 reviewed MCQs** (at least 2 patterns × (2 detectors + 2 reserved checkpoints), plus ≥4 ordinary items), ≥2 lessons, 1 safe SQL task. If independent reviewer exists, mark their work; otherwise report second review unavailable rather than faking it.

**Tests:** `python scripts/validate_content.py --strict --stage S1`, backend integration and hostile SQL suite, frontend build/test/E2E, migration fresh DB, reset→seed→verify, repeat after restart. CI thereafter includes S1 stage gate. **S1 exit:** all tests actually green; owner review complete. If review missing, label S1 `blocked` and report working engineering subset—do **not** mark complete.

---

## After S1

Write `docs/stage_tasks_S2.md` as task-sized acceptance criteria from §12 of the master plan. Continue stage order, keeping the seeded demo and strict validator in every subsequent stage boundary. S3 adds approved-lesson and cleared-section FTS5/BM25, citations and curated tutoring. S5 adds the mandatory Qwen3 Ollama integration and opt-in real-model check. Keep S1 independently runnable with curated remediation. `IMPLEMENTATION_STATUS.md` is the factual test log; do not invent completed tasks or dates.
