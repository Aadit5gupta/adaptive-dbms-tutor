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

| D10 | 2026-11-23 | Enable the SQL worker on tested Apple Silicon macOS | macOS rejected RLIMIT_AS; SQLite hard heap cap plus tested CPU, file and descriptor limits still apply | Unverified platform support | Other platforms use worker-unavailable state |

| D11 | 2026-11-23 | Allow two-pass `ai_verified` originals in local learning and preserve human-only gates | Owner authorized post-build activation. Exact chapter evidence, separate-context review and independent SQL checks support the initial bank | Treating AI review as human sign-off or clearing book text during factual review | Learner gates use explicit `--review-policy learner`. Human pilot review and section-rights approvals retain their existing requirements. |

| D12 | 2026-11-23 | Keep open assessment hints and the original JOIN count mismatch explanation curated | Actual Chrome sessions exposed repeated incomplete hints and an incorrect COUNT recommendation from the small model | Giving all generated output the same instructional weight | The curated prompts preserve answer and evidence boundaries. Other eligible DBMS and SQL tutoring still uses the bounded local provider. |

| D13 | 2026-11-25 | Fill the 16 empty Learn topics with introductory lessons and ordinary practice | The owner requested usable material in the pending Learn subsections | Expanding assessment and misconception coverage in the same change | All 24 topics have material. The new questions are ordinary practice and use the existing learner review and attribution policy. |

| D14 | 2026-11-25 | Permit section-scoped publisher-license verification for the two bundled excerpts | The owner requested searchable textbook material without a human approval step for these verified licenses | Blanket book clearance or fabricated human approval | Exact scope, publisher terms, attribution and bytes are pinned. Only the two defined excerpts use the new path. The human clearance workflow applies to other candidate sections. |

| D15 | 2026-11-25 | Add SHA-256-pinned Shea Chapter 8 and DataField Chapter 26 excerpts | The owner asked to resolve the remaining sources. Shea lists a noncommercial license and DataField Chapter 26 carries an explicit CC BY-SA 4.0 footer | Whole-book import and assuming the OpenStax notice is inapplicable | Four distinct book sources now have one searchable excerpt each. The Shea excerpt is for noncommercial use. OpenStax remains link-only pending written permission. |

| D16 | 2026-11-25 | Use the existing FTS index for matched Library previews and filter by source before ranking | Book and lesson titles used to lead to similar external links, and leading excerpts could omit the match | A separate search service or client-side filtering of truncated results | Preserve the existing tutor passage and provenance pipeline. Library results distinguish in-app lessons from publisher excerpts and pass a topic with an editable question to Ask Tutor. |

| D17 | 2026-11-25 | Separate one-click and typed clues in open practice items | The prepared hint ignored the required question text | Sending a learner's request and the open assessment to the LLM | Prepared hints advance through three levels. Typed requests match curated reasoning prompts for recognized wording on the authorized topic and fall back to the general hint. Existing level 2/3 evidence rules apply. |

## Deviations and blockers

| Date | Stage/task | Problem / deviation | Impact | Fallback | Owner action required |
|---|---|---|---|---|---|
| 2026-11-23 | S0.1 / S5 | Ollama CLI unavailable at bootstrap | Real-model acceptance remained pending | Owner installed Ollama and `ollama list` confirmed `qwen3:1.7b` on 23 November 2026 | Run the opt-in real-model check after S5 integration |

| 2026-11-23 | S0.6 and later pushes | GitHub rejects workflow creation with current CLI OAuth token | Initially delayed commits and CI | `workflow` scope confirmed and queued commits pushed successfully on 23 November 2026 | Resolved |
| 2026-11-23 | S1.8 | Initial lessons, questions and SQL output artifacts await human verification | Historical human-only S1 gate remained open | D11 adds a learner-policy route after separate-context verification | Human review remains pending for the human-only gate |

Never invent the owner's approval, manual review, license clearance or human pilot enrollment.
