# DBMS Mentor — decisions and owner constraints

**Design authority:** `MASTER_PLAN.md` v1.2. This is a living decision log, not a second architecture plan. Do not treat defaults as facts about the user.

## Owner-supplied constraints

| Constraint | Current value | Until confirmed |
|---|---|---|
| Submission deadline for **this DBMS tutor** | unconfirmed | Conservative ≤8-week *planning assumption only* |
| Available build hours per week | unconfirmed | Solo, part-time |
| Human second reviewer for question/lesson checks | unconfirmed | None; mark `second_review=false` |
| Deployment target | Local-first | No public SQL execution |
| Development machine | 8 GB MacBook Air (owner-supplied) | Test SQL restrictions before enabling learner SQL |
| Bootstrap CLI versions | macOS 27.2.1 (26B131) arm64, Python 3.12.16, Python SQLite 3.54.1 with FTS5/BM25, system SQLite CLI 3.54.0, Node 26.13.1, npm 11.20.0, Git 2.56.1, gh 2.104.0, uv 0.13.8 | App compatibility still to be tested |
| Faculty approval for human pilot | unconfirmed | No real participant pilot |

**Scope rule:** If fewer than four weeks remain, retain the S0–S6 core (with authored lessons and catalog links when S3 source clearance is blocked). If the owner confirms ≥3 months and a reviewer, unlock expanded seven-domain content, but do not compromise core correctness. Never treat unrelated project deadlines as this project's submission date.

## Recorded decisions

| ID | Date | Decision | Rationale |
|---|---|---|---|
| D01 | 2026-11-22 | `MASTER_PLAN.md` v1.2 only product/architecture authority | One canonical implementation contract |
| D02 | 2026-11-22 | Five catalog sources; indexed count must be derived from successfully searchable sections | Avoid misleading rights/coverage claims |
| D03 | 2026-11-22 | Local FastAPI + React + SQLite FTS5, no required Docker/cloud/paid API | Zero-budget modular monolith |
| D04 | 2026-11-22 | S1 includes first browser-visible misconception + SQL demo | Differentiating feature available early |
| D05 | 2026-11-22 | Staged content gates: `--strict` structural; `--stage S1/S4` minimum coverage | Do not claim completeness from empty YAML |
| D06 | 2026-11-22 | Dedicated demo DB and idempotent short attempt transactions | Protect user data and state consistency |
| D07 | 2026-11-22 | SQL worker must pass platform-specific hostile-input tests; no public deployment claim | Restricted subprocess is defense-in-depth, not certified security isolation |

## New decisions (append only)

| ID | Date | Decision | Reason | Alternative rejected | Impact |
|---|---|---|---|---|---|
| D08 | 2026-11-23 | Mandatory Ollama tutoring with `qwen3:1.7b`, FTS5 BM25 retrieval, and curated fallback | Owner update supersedes the optional LLM language in the supplied v1.2 spec and S5 status | Optional model and paid inference | S3 grounding and S5 real-model demonstration required; deterministic assessment retains authority |
| D09 | 2026-11-23 | Initialize Git inside the extracted specification directory | Keeps the original archive and parent folder outside the repository | Tracking surrounding files | Use the extracted directory for all commands |

## Deviations and blockers

| Date | Stage/task | Problem / deviation | Impact | Fallback | Owner action required |
|---|---|---|---|---|---|
| 2026-11-23 | S0.1 / S5 | Ollama CLI unavailable at bootstrap | Real-model acceptance remains pending | Curated path and mock tests during development | Install Ollama and manually pull the configured model before real-model verification |

Never invent the owner's approval, manual review, license clearance or human pilot enrollment.
