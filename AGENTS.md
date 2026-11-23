# Codex agent operating rules — DBMS Mentor

**Authority:** `MASTER_PLAN.md` v1.2 is the **only architectural/product authority**. This document is an operating checklist, not a competing plan. `content/manifests/books.yaml` and authored content are rights/content **data**. If any supporting file contradicts the master plan, stop the conflicting change, record it in `DECISIONS.md`, and follow `MASTER_PLAN.md`.

**Starting stage:** S0. **Do not mark a task green without actual executed tests.**

## Before doing any work

1. Read **all of `MASTER_PLAN.md` once** at bootstrap, then this file, `DECISIONS.md`, `IMPLEMENTATION_STATUS.md`, and `docs/stage_tasks_S0_S1.md`. On later stages, reread applicable sections and record affected contracts; don't ignore relevant sections solely because of a reading table.
2. Inspect the existing repository; **never overwrite/delete unrelated code or user files**. Older project plans are superseded; move them outside the active implementation docs only after confirming they are safely retained or Git-tracked. Don't force-push, rewrite history, or delete user data without owner approval.
3. Confirm Python, SQLite, Node, npm, Git, OS and local CLI versions and log exact versions in `DECISIONS.md`. No automatic purchase, account signup, Docker or multi-GB Ollama download.
4. Use the exact provided file tree. Stage S0 tasks first; no major refactor or whole-project code dump.

## One task at a time

For each task, write in your response: target files, behavior, tests/acceptance criteria and any rights/content blocker. Implement a small vertical change with tests, run the tests, update `IMPLEMENTATION_STATUS.md` with actual commands/results/date, log nontrivial decisions, and commit using `S<n>.<task>: ...` only when green. Report actual progress and blockers; avoid autonomous unbounded loops.

## Invariants

- **AI is not the authority:** LLMs never grade, publish educational material, alter mastery/misconception state, decide policy or invent citations. You may *draft* questions and lessons, but an LLM may never set `author_verified` or `independent_verified`; the owner must explicitly verify content.
- **Content enums:** review `draft|author_verified|independent_verified`; pools `diagnostic|practice|checkpoint|pre_test_a|post_test_b`. `detector` is a role via mapped wrong options, not a pool. Misconception *definition* has boolean `enabled`; *learner* state `possible|active|improving|resolved`. Stable reference `logical_id@version` (positive integer); versions are immutable.
- **Misconception gate:** enabled/approved definition requires 2 detector **logical IDs**, 1 approved remedial lesson, 2 distinct reserved unseen checkpoints, valid evidence mappings/rights. `python scripts/validate_content.py --strict` verifies structure/coverage; `--stage S1`/`--stage S4` verify actual stage minima. An empty set of enabled rules is NOT sufficient for S1.
- **Rights:** five catalog records do not mean five indexed books. Import requires per-section, hash-matched approved clearance. BCcampus Chapters 10 and 11 need extra review; DataField remains link-only absent documented permission. Counts come from successful FTS imports, not clearance records. No uncleared book text in Git.
- **SQL:** learner SQL executes **only** in a killable restricted subprocess against disposable *read-only exercise fixtures*, never the app DB. Implement parser + authorizer/table/function allowlists, `setlimit`, progress handler, row/output caps, process wall timeout and tested OS resource restrictions before enabling SQL submissions. Unsupported platform → disable untrusted SQL worker and document. A worker/LLM must NEVER run inside an app DB write transaction.
- **Attempts:** immutable question versions, stable session-item allocations, one committed submission per session item, user+idempotency-key uniqueness, same-key different payload → 409. SQL grade in worker first; then in one short immediate SQLite write transaction store grade, attempt, mastery history, misconception evidence, policy decision and recommendation. Never double count.
- **Demo safety:** `scripts/reset_demo.py`, `seed_demo.py`, `verify_demo.py` only operate on a dedicated demo SQLite path, refuse any regular app DB path, and preserve non-demo user records. Run demo E2E at each stage boundary from S1. Before S4, demo UI is dev loopback-only, NOT an anonymously accessible public multi-user app.
- **Tests and privacy:** no fake test results, no leaked answer keys/hidden SQL fixtures, no fabricated book rights, no analytics superiority claims. Hide auth secrets/learner SQL in logs. Add CSRF Origin/Referer checks with same-origin cookies by S4, plus account isolation and `/me/export`/`/me/delete`.

## Run at stage boundaries

- `python scripts/validate_content.py --strict` plus `--stage S1` or `--stage S4` when asserting that stage complete
- Backend unit/integration/adversarial tests, Ruff and type checks supported by the repo
- Frontend lint/typecheck/build/Vitest; browser demo E2E when available
- Real Alembic migrations on a fresh DB
- `python scripts/reset_demo.py && python scripts/seed_demo.py && python scripts/verify_demo.py` from S1, using the safe demo DB path
- Update `IMPLEMENTATION_STATUS.md`, `DECISIONS.md`, and `docs/test-report.md` with commands, dates and actual results

**First instruction:** Inspect the repo and the supplied docs. Start `S0.1` from `docs/stage_tasks_S0_S1.md`, report what passed, and proceed to the next small task only after confirming the current task passes. Do not ask the owner to repeat already documented decisions. Ask only for actions that require genuine human verification or external permissions.
