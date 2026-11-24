# DBMS Mentor — Codex Master Build Plan (Single Source of Truth)

**Status:** Consolidated implementation specification, v1.2 · updated 23 November 2026
**Audience:** Codex / coding agents + student developer
**Mission:** Build a genuinely useful, **zero-paid-service-required**, **misconception-aware**, adaptive DBMS + SQL tutor. Deliver a dependable vertical slice first, then a polished final-year major project with honest evaluation.
**Supersedes and replaces:** v1.0, `PLAN.md`, `PLAN_PHASE2.md`, and separate review notes. **`MASTER_PLAN.md` v1.2 is the only build authority.** Remove/rename obsolete plans in the repository during bootstrap rather than leaving competing instructions. The machine-readable `content/manifests/books.yaml` is source-rights data, not a competing project plan.

> **Start with S0, then build in stage order.** Do not ask for design decisions already answered here. When a third-party book cannot be imported legally or a model cannot run, implement the documented fallback and log the blocker. Never invent successful test results, educational sources, licenses, or research outcomes.

---

## 0. Product contract

**One subject:** Database Management Systems, including SQL. No OS, networks, OOP, DSA, or generic multipurpose learning platform.

**Primary user story:** A learner joins, takes a diagnostic, sees subtopic-level weaknesses, is offered a justified next step, learns using attributed DBMS source material, practices theory and real SQL, receives targeted misconception-aware feedback, and sees mastery and recommendations change over time.

**Product pillars:**
1. **Learn:** approachable, well-structured concept lessons with worked examples, glossary and source references.
2. **Assess:** curated single-answer MCQs and executable SELECT-only SQL exercises; authoritative answer keys are never supplied by the LLM at runtime.
3. **Diagnose:** track topic/subtopic mastery, confidence, question history and *evidence-based*, specific misconceptions.
4. **Adapt:** an auditable Python policy chooses what to learn/practice next, checks prerequisites and content availability, avoids repetition and explains its decision.
5. **Tutor:** grounded explanations and progressive hints using a five-record source catalog and only approved indexed passages (target two indexed books initially); required Ollama tutoring with an offline curated fallback.
6. **Improve:** useful dashboards, learning history, scheduled review and an evaluation harness; a small human study, if conducted, is an exploratory feasibility pilot, never assumed evidence of effectiveness.

**Definition of the first successful end-to-end demo (S1):** In a minimal browser screen, Learner A makes two distinct wrong choices revealing **KEYS-02** (incorrectly assumes a foreign key must be unique), sees cautious feedback and an author-approved remedial example, then answers two previously unseen checkpoint questions and receives a changed recommendation and persistent history. Learner B has different evidence about **SQL-JOIN-01** and receives another next action; a real restricted SQL LEFT JOIN exercise is graded against hidden fixture(s). The demo is deterministic, synthetic, isolated from real user data, and runnable offline. S1 cannot be claimed complete from API tests alone.

**Not in the initial product:** Payments, social feed, mobile app, voice/video, unrestricted SQL DDL/DML, user-uploaded arbitrary books, auto-publishing AI questions, distributed microservices, mandatory cloud APIs, custom LLM training, deep knowledge tracing, live classroom analytics.

**Non-negotiable rule:** `LearnerModel` estimates; `AdaptivePolicy` recommends; `Retriever` supplies source passages; `TutorProvider` communicates; `AssessmentGrader` judges answers. The LLM NEVER grades authoritative answers, determines final mastery, changes policy state, fabricates citations, or silently modifies the curriculum.

---

## 1. Fixed stack and operating constraints

| Area | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite + React Router | Familiar, simple SPA |
| UI | Tailwind CSS, accessible headless primitives as needed, Lucide icons | Consistency without a heavy component framework |
| Fetch/state | TanStack Query + small local UI state | Avoid manual caching complexity |
| Backend | Python 3.11+ + FastAPI + Pydantic v2 | Typed contracts and testability |
| App database | **SQLite**, SQLAlchemy 2.x, Alembic | Local-first, no paid service, no DB server |
| Search | **SQLite FTS5**, BM25 ranking + topic filters | Free and adequate baseline for curated content |
| Book extraction | PyMuPDF for permitted PDFs; BeautifulSoup for permitted HTML | Preserve section/page provenance |
| LLM | `TutorProvider` with Ollama (`qwen3:1.7b` by default) and offline `CuratedProvider` | Fully functional without AI or API keys |
| SQL lab | Separately launched restricted Python worker + temporary **read-only SQLite exercise DB** | Never execute learner SQL against app DB |
| Tests | Pytest (unit/API/integration), Vitest + Testing Library (UI), Playwright (one core E2E flow if practical) | Verify core behavior |
| Quality | Ruff, mypy where practical, ESLint, TypeScript check, GitHub Actions CI | Agent-safe iteration |
| Runtime | Local Mac/Windows/Linux; frontend & backend launched separately with documented commands | No Docker necessary |

**Zero-cost means no mandatory paid APIs, hosting, model inference credits, or subscriptions.** Developer machine, electricity and internet are not literally free. Public hosting, concurrent arbitrary SQL submissions, and unlimited hosted LLM usage are explicitly not guaranteed. Do not imply otherwise.

**Architecture:** One modular monolith. The browser communicates only with FastAPI. FastAPI owns account handling, course content, grading, attempts, learner state, adaptive choices, retrieval and tutor orchestration. SQLite FTS5 lives in the app DB. SQL exercises run in a distinct restricted worker and in disposable DB fixtures. No Redis, Celery, vector DB, Kubernetes or Docker for MVP.

**Local authentication (S4, after core learning loop):** use a vetted Argon2 password hashing library and an opaque-token server-side session table. Cookie: HttpOnly, SameSite=Lax, Secure in HTTPS deployments. Prefer same-origin SPA/API in deployable builds; configure the Vite development `/api` proxy so frontend-origin requests stay same-origin from the browser's perspective. All state-changing requests must validate `Origin` against an explicit allowlist; permit a missing Origin only through a strictly checked same-origin `Referer` fallback; reject requests missing both rather than silently bypassing CSRF protection. Never trust SameSite alone. Disable cross-origin credentialed CORS by default. Add tests for cross-site and missing headers; use CSRF tokens if deployment/integration constraints make origin checks unreliable. Rate-limit login; expire/logout sessions; no auth secrets in localStorage. Demo accounts are only seeded in dev and never hardcoded into production. No promises of safe public internet exposure without security review.

**AI model selection:** The application defaults to `TUTOR_PROVIDER=ollama` and `OLLAMA_MODEL=qwen3:1.7b`, using Ollama's local `/api/chat` endpoint on loopback. `TUTOR_PROVIDER=curated` explicitly selects offline tutoring. Developers install Ollama and pull weights manually. The application and CI never download weights or call external AI APIs. When Ollama is missing, busy, times out, returns unusable output, or has no suitable evidence, serve a curated explanation with visible status and genuine attribution where available.

**8 GB MacBook Air baseline:** Start with one in-flight inference, a 4,096-token context, an output cap of 384 tokens, thinking disabled, and a 30-second total request deadline. Bound learner input, include at most three recent user/assistant pairs and four retrieved passages in the prompt, and truncate older history first. Reject excess simultaneous inference with immediate curated fallback. Keep the model briefly loaded for follow-ups and allow idle unloading. CI uses a mock provider. Final acceptance requires a separately invoked real-model smoke check and a documented local tutoring demonstration.

**Retrieval upgrades:** Implement `Retriever.search(query, topic_ids, k)` interface now. First implementation FTS5. Optional local embeddings/hybrid retrieval only after a labeled retrieval evaluation demonstrates improvement. No premature pgvector.

---

## 2. User experience / product surface

Navigation: **Dashboard · Learn · Practice · SQL Lab · Library · Progress**, plus a contextual **Ask Tutor** control. Desktop-first but responsive; accessible keyboard navigation, screen-reader labels and contrast. Design: polished neutral/light theme, one accent color, excellent typography, clean spacing, progress states, fast page loads, no meaningless gamification.

**Screens:**
- **Welcome/Account:** sign-up/login and guest demo entry (demo data clearly isolated); local-only notice.
- **Onboarding:** objective (exam/placements/understanding), skill level, optional daily time; preferences personalize phrasing/suggested time, not fake mastery.
- **Diagnostic:** 14–21 approved questions as a **seven-domain screening**, never claimed to accurately diagnose all ~35 subtopics. After weak/domain-level answers, the policy offers targeted follow-up subtopic probes on distinct questions. Show unknown/low-confidence concepts; do not seed unsupported confidence.
- **Dashboard:** meaningful "What should I do next?" card including *why*, mastery by topic, weak subtopics, active misconception hypotheses, continue previous session, recent progress.
- **Learn:** topic tree, prerequisite indicators, concise curated lessons, examples/tables, contextual tutoring, practice CTA. Do not prevent browsing locked concepts.
- **Practice:** 5-question resumable session, single question at a time, submit → grade → feedback, progressive hints, "Why is my answer wrong?", optional source excerpt; attempt history and next recommendation.
- **SQL Lab:** schema explorer, example rows, CodeMirror SQL editor, Run/Submit, readable result grid, expected-vs-actual differences when pedagogically appropriate, safe timeouts, feedback and linked concepts.
- **Library:** five catalog records, with verified rights/index status, topic search across actually indexed passages, attribution and link to originals. Chapter navigation is deferred; do **not** claim full-book viewing or five indexed books. Display `X of 5 indexed` based on real imports.
- **Tutor:** mode `explain`, `simpler`, `hint`, `example`, `ask`; reply includes source references. LLM/curated status clearly visible.
- **Progress:** attempts, practice time, topic/subtopic trend, possible/active/resolving misconception hypotheses, review-due items and honest low-confidence flags.
- **Study/evaluation mode** (later, optional human pilot): voluntary consent, matched fixed-versus-adaptive assignments and held-out pre/post test forms; no powered efficacy claims without adequate design and data.

**Quality bar:** loading, empty and error states throughout; no dead buttons; persist progress across refresh; backend-generated recommendations only; clear failure messages; no fabricated badges or improvement claims.

---

## 3. Curriculum and competency graph

Seven high-level domains preserve the uploaded plan's simple dashboard, with **subtopic-level nodes** for actual diagnosis and targeted tutoring. Define IDs/slugs in YAML, not in components.

| Domain | Initial subtopics / competencies | Main question type |
|---|---|---|
| ER modeling | entities, attributes, relationships, cardinality, weak entities | MCQ / scenario |
| Relational model | relations, candidate/primary/foreign keys, constraints, selection/projection, relational joins | MCQ / worked examples |
| SQL | SELECT/WHERE, ORDER BY, GROUP BY/HAVING, INNER/LEFT JOIN, subqueries, NULL, aggregates | MCQ + executable SQL |
| FDs & normalization | functional dependencies, closure/candidate keys, 1NF/2NF/3NF/BCNF, anomalies, lossless decomposition | MCQ / scenarios |
| Transactions | ACID, schedules, conflict serializability, recoverability | MCQ / scenarios |
| Concurrency | locks, 2PL, deadlocks, isolation anomalies | MCQ / scenarios |
| Indexing | clustered/nonclustered, dense/sparse, B/B+ trees, hash indexes, basic plans | MCQ / scenarios |

**Later additions**: advanced SQL (CTEs/window functions), query optimization, recovery, fuller DBMS topics. These should extend the curriculum but not block the primary loop.

**Prerequisite edges** (curated, editable YAML): relations/keys → joins; SELECT/WHERE → joins/aggregation; FDs → normalization; candidate keys → 2NF/3NF; transactions → concurrency; relational model → indexing. Avoid declaring advanced SQL prerequisites for core theory unless warranted. Detect cycles in CI.

**Staged content budgets (authoring starts in S0, not after plumbing):**
- **S1 walking skeleton gate:** two fully enabled/approved misconception patterns, each with ≥2 independent detector questions, ≥1 reviewed remediation lesson and ≥2 distinct *unseen* checkpoints; **≥12 publication-eligible MCQs total** (8 dedicated detector/checkpoint items + ≥4 ordinary practice items), ≥2 lessons and ≥1 runnable, independently expected-result-checked SQL LEFT JOIN task. Additional 18–24 MCQs and 2–3 lessons are a useful near-term target, **not** a precondition for demonstrating the first loop. Do not self-approve synthetic/draft content.
- **Lean MVP / default solo build:** three connected areas (keys, FDs/normalization, SQL SELECT/JOIN), **≥30 reviewed MCQs**, **≥6 SQL exercises**, **≥6 curated lessons**, **≥3 fully covered misconception patterns**, plus a seven-domain screening only where genuine reviewed material exists. Other domains can be browsed but remain explicitly undercovered.
- **Expanded campus demo (only if time/review allows):** seven domains with balanced domain-level screening (14–21 questions), **≥80 reviewed practice MCQs**, **≥20 SQL exercises**, **≥12 lessons**, **≥6 complete misconception patterns**.
- **Stretch (never required for graduation):** 120–180 reviewed MCQs, 30–50 SQL tasks, 20–30 lessons, 20+ supported misconception patterns and research content. Counts never outrank correctness, safety, or source provenance.

**No reviewer/date invented:** Submission deadline, hours/week and availability of a second reviewer remain **unconfirmed**. Until explicitly entered into `DECISIONS.md`, run a **solo, zero-budget, ≤8-week planning envelope** and enforce only the lean MVP gates. This is a planning assumption, **not a claim about the user's actual deadline**. If fewer than four weeks remain, prioritize S0→S6 core work before all expansion; if independent review and ≥3 months are confirmed, unlock expanded goals. Do not let missing details block S0 scaffolding.

**Content review policy:** Original authoring begins in `draft`. Two AI passes, with the second using a separate context, may qualify original material as `ai_verified` for local practice, diagnostics, checkpoints, remediation and the learner demo. Both passes check the exact published chapter, answer or lesson content, ambiguity and, where relevant, misconception and assessment independence. Independently derive SQL expectations and execute reference and alternative correct queries on every fixture. Record item dispositions and leave failures in draft. Original examples and exercises may cite chapters as factual references. Book excerpt ingestion requires a section-specific rights record and matching bytes under §4.

**Human sign-off:** Only an actual human may record `author_verified` or `independent_verified`. Prefer independent human review where available and require it for higher-stakes pilot assessments before data collection. Machine verification carries named AI review passes and an actual verification date. Synthetic test content remains under `tests/fixtures`. Live tutor outputs cannot change publication status.

---

## 4. Five-source digital library, verified licenses and provenance

**License check date:** **2026-11-22**. These are publisher-page observations, not a complete audit of all chapters/images/datasets. The current metadata belongs in `content/manifests/books.yaml`. Its `rights_status` initially remains `link_only` for every source until individual import segments receive explicit clearance. Exactly five catalog entries are expected, while **indexed count is factual and can be zero at bootstrap**.

| Book ID | Work and official page | Publisher-stated license | Crucial limitations / source observations |
|---|---|---|---|
| `bccampus_db_design_2e` | Adrienne Watt and Nelson Eng, *Database Design, 2nd ed.* — https://opentextbc.ca/dbdesign01/ | **CC BY 4.0** except otherwise noted; https://opentextbc.ca/dbdesign01/ | **Chapter 10 ER Modelling** credits a derivative of *Relational Design Theory* by Nguyen Kim Anh (CC BY 3.0); **Chapter 11 Functional Dependencies** has third-party **CC BY-SA 3.0** derivative attribution from Wikipedia. Audit both independently; do not treat them as uniformly CC BY 4.0. Book cover additionally credits a CC BY-SA 2.0 image; exclude covers/images by default. |
| `runestone_practical_db` | Christopher Painter-Wakefield, *A Practical Introduction to Databases* — https://runestone.academy/ns/books/published/practical_db/index.html | **CC BY-SA 4.0**; license notice on index page | Cover credits an Unsplash photographer; do not import cover or external datasets without separate review. Book text is a priority candidate for controlled section import. |
| `shea_pop_culture_sql` | Brendan Shea, *SQL and Database Management Through Pop Culture* — https://brendanpshea.github.io/database_sql/ | **CC BY-NC 4.0** stated on homepage | Noncommercial restriction; separately inspect chapter assets, embedded notebook code, datasets, brand/media images, third-party notices; do not infer every included asset is licensed under the book notice. |
| `openstax_foundations_is` | OpenStax, *Foundations of Information Systems* — https://openstax.org/books/foundations-information-systems/pages/preface | **CC BY-NC-SA 4.0**; explicitly described in preface | Noncommercial and share-alike restrictions on adaptations; per-figure credits may differ. Only DBMS-relevant text; exclude art unless separately cleared. |
| `datafield_db_fundamentals` | DataField.Dev, *Database Fundamentals* — https://datafield.dev/sql/ | **CC BY-SA 4.0** per the Chapter 26 footer, verified 2026-11-25 | The scoped Chapter 26 excerpt may be indexed. Other text and assets require their own rights records. |

**Policy:** A five-book *catalog* is not five *indexed* sources. S1 requires one cleared passage or original source-linked lesson eligible for learner publication; S3 targets **searchable passages from two books with separate section-level rights records**; the third is optional; five fully indexed works are stretch only. The UI displays real indexed count and exact permissions. NC content should not be incorporated into a commercial offering without permission or replacement; a college assignment is not blanket permission for any use. Use separately licensed works as a **collection**, retain per-passage provenance and obligations, and do not automatically remix works with incompatible share-alike conditions. LLM paraphrases that reproduce protected expression may be adaptations: do not silently publish them as rights-free.

**Rights gate before every import:** Inspect the exact chapter/section, text, images, tables, code, examples, datasets, source terms and attribution; record `section_url`, `accessed_on`, `license_url`, `rights_status`, `exceptions`, `reviewer`, `reviewed_on` and `approved_content_hash` in a per-section clearance record. If exceptions are unresolved, mark section `link_only` / `blocked_pending_review`, and do not index it. Start with clean text-only chapters from BCcampus and Runestone; **BCcampus Chapters 10 and 11 remain pending separate rights review**. Keep source text outside Git until cleared. Save the precise findings, not a blanket `approved_local_index` for the whole book.

**Publisher license verification, 2026-11-25:** The owner authorized a second rights path for specific text excerpts with clear reuse terms. Record `publisher_license_verified` only for an explicitly supported section and its published license. Record the actual verification date and verifier as `ai:...`, include attribution, and match the exact excerpt bytes. The verified scopes are the Runestone foreign-key enforcement excerpt, the BCcampus Chapter 9 orphan-record excerpt, Shea Chapter 8's index storage excerpt for noncommercial use, and DataField Chapter 26's transaction atomicity excerpt. Unresolved exceptions and permission-specific sources still require the original clearance workflow. Human sign-off for educational assessments remains separate.

**Pipeline:** cleared PDF/HTML → extract with page/heading anchors → remove unlicensed figures/boilerplate → section-aware chunks (~250–450 words) → explicit topic IDs → SQLite FTS5 and metadata. Chunks use source ID, section URL and hash for idempotent reindexing. Import scripts run offline, not via learners' HTTP requests. A failed import cannot silently count as indexed.

**Retrieval:** `Retriever.search(query, topic_ids, k)` uses FTS5 (`bm25`) and filters on cleared indexed chunks, retrieving top 4–6 with relevance threshold and broader fallback. When no passages exist, answer from independently authored approved lesson material with clear labeling, or say evidence unavailable. UI citations are assembled from real stored metadata, never model-invented references; treat retrieved text as untrusted prompt content.

**Tutor response:** Ollama supports personalized explanations, simpler explanations, open-ended hints, SQL mistake explanations, examples and natural-language follow-ups. In-progress assessment items use curated progressive hints. Observed repeated SQL misunderstandings may use a specific reviewed explanation after grading. Give a concise answer grounded in human-reviewed or AI-verified original lessons or hash-matched, individually cleared book sections. The application provides stable attribution from retrieved records and chooses any approved checkpoint. Pass only bounded, authorized context such as the topic, learner goal, current misconception hypothesis and safe post-grade error category. Withhold assessment answers, reference SQL, hidden fixtures, credentials and unrelated learner data. A tutor response cannot alter grades, mastery, misconception evidence or recommendations. Curated tutoring works offline. Defer caching until inference evidence warrants it.

**Primary license evidence (checked 2026-11-22):** https://opentextbc.ca/dbdesign01/ ; https://opentextbc.ca/dbdesign01/chapter/chapter-11-functional-dependencies/ ; https://runestone.academy/ns/books/published/practical_db/index.html ; https://brendanpshea.github.io/database_sql/ ; https://openstax.org/books/foundations-information-systems/pages/preface ; https://datafield.dev/sql/ . License texts: https://creativecommons.org/licenses/by/4.0/ ; https://creativecommons.org/licenses/by-sa/4.0/ ; https://creativecommons.org/licenses/by-nc/4.0/ ; https://creativecommons.org/licenses/by-nc-sa/4.0/ . Further section audits remain required.

---

## 5. Learner model: evidence without overclaiming

Keep **all attempts append-only**. Mastery is a score, **not a scientifically calibrated probability of knowing a concept**. Store per-user/per-subtopic `score ∈ [0,1]`, `attempt_count`, `distinct_question_count`, `recent_accuracy`, `last_attempt_at`, `confidence_level = insufficient|emerging|supported`, and `model_version`. Domain mastery is a coverage-aware aggregation and must show number of assessed subtopics.

**Baseline model:**

`new_score = clamp(old_score + alpha * weight * (evidence - old_score), 0, 1)`

Defaults `old_score = 0.5`, `alpha = 0.20`, evidence `1` for correct and `0` for wrong. Boundary simulation is mandatory: first wrong → `0.40` exactly (not `<0.40`); successive correct → `0.60`, `0.68`, `0.744`. Keep score-based thresholds explicitly inclusive/exclusive; do not let one answer claim mastery. **For v1, difficulty weight = 1.0**; difficulty is logged for future experiments. Repeated identical questions should contribute little or no additional confidence. Return mastery before/after with the attempt, but do not translate a one-question movement into "learned". Determine confidence from **distinct** independently attempted questions, e.g. `insufficient (<3 distinct)`, `emerging (3–5)`, `supported (≥6)`; thresholds are engineering policies to validate. Record separate diagnostic vs practice evidence and avoid treating hints as independent successes.

**Attempt types:** diagnostic / practice / SQL / held_out_pre / held_out_post. Held-out test items should **not update training mastery during an experiment**, unless explicitly part of standardized diagnostic seeding for both arms; keep inference and evaluation roles clear. Track question version and content origin.

**Model interface** (implement early, only one model at first):

```python
class LearnerModel(Protocol):
    name: str
    def initialize(self, subtopic_id: str) -> dict: ...
    def predict(self, state: dict, question: QuestionMeta) -> float | None: ...
    def update(self, state: dict, question: QuestionMeta, evidence: AttemptEvidence) -> dict: ...
    def summarize(self, state: dict) -> MasteryView: ...
```

Add BKT or Elo/IRT **only after** baseline tests and enough validation data; fit parameters on training learners and evaluate on held-out learners, never invent model superiority. If no useful data, document why model upgrade remains experimental.

**Consistency:** The `POST attempt` command validates ownership and unique submission idempotency key, computes authoritative grade, writes attempt, updates `mastery`, adds `mastery_history`, persists a policy decision and creates recommendation **atomically in one app DB transaction**, using SQLite `BEGIN IMMEDIATE` or an equivalent explicitly tested immediate write transaction. Duplicate retries return the same committed outcome without double-counting. Keep transactions short; do not run an LLM or a SQL sandbox subprocess while holding the app DB write lock.

---

## 6. Misconception-aware intelligence (must be working in final product)

A misconception is a **specific, testable knowledge hypothesis**, not "answered something wrong" or "low mastery". The system must avoid claiming certainty.

**Canonical statuses and records (never conflate these):**
- Content `review_status`: `draft | ai_verified | author_verified | independent_verified`. `ai_verified` requires original material, exact catalog chapter provenance and separate-context AI review metadata. The two human statuses require a real human identity and keep the existing review workflow.
- Misconception **definition**: `code`, `subtopic_id`, `name`, `explanation`, `review_status`, `enabled` (boolean), `evidence_rule`, `detector_question_refs`, `remediation_lesson_ref`, `checkpoint_question_refs`, `retrieval_query`, `source`. `enabled=true` only for a fully reviewed, complete rule.
- **Per-learner** state in `user_misconceptions.state`: `possible | active | improving | resolved`; absent record means no evidence. `active` is NEVER a content-definition review status.
- Examples: `KEYS-02` (foreign key assumed unique), `SQL-JOIN-01` (INNER vs LEFT JOIN), `NORM-03` (partial vs transitive dependency), `SQL-NULL-01` (`= NULL` vs `IS NULL`), `TXN-01` (atomicity vs durability).

**Canonical version reference:** `logical_id@positive_integer_version`, e.g. `q_keys_fk_001@1`. One SQL task is a question with `type=sql`, and lessons are likewise referenced by immutable version. A duplicate `(logical_id, version)` fails validation; two versions of one logical question **never count as two independent detector signals**. All rule references, assessment allocations, answers and attempt rows resolve a specific immutable version.

**Evidence:** An approved MCQ distractor may identify at most one specific misconception. Two distinct **logical question IDs**, independently answered incorrectly with the mapped distractor and without answer-revealing hints, are necessary for `active`. One signal sets `possible`. Replaying one question, or merely changing its version, cannot multiply independent evidence. A wrong SQL query can provide an error category or cautiously worded clue, but one result mismatch is NOT a proven conceptual misconception; only separately validated, discriminative SQL signatures can contribute structured evidence. Record attempt ID, logical question ID and version, detected code, evidence reason and detection method.

**Remediation:** For an active hypothesis with approved lesson + checkpoints, show a contrasting example, then allocate reserved checkpoint questions that the **individual learner has never encountered**. Two independent correct, unhinted checkpoints can set `resolved`; otherwise use `improving` conservatively. If approved unused checkpoints are exhausted, do not fabricate a question or mark the misconception resolved; recommend general practice or authoring more checkpoints. Preserve historical evidence. Do not trap the learner; allow skip and other-topic override.

**Content gates:** `python scripts/validate_content.py --strict` checks structural/semantic integrity and fails when **any `enabled=true` definition** lacks two distinct *approved* detector logical question IDs with a mapped wrong distractor, one approved remediation lesson, two distinct approved reserved checkpoint IDs, valid version references, non-overlapping assigned roles, and valid rights/source metadata. It also rejects drafts in production selection, missing topic IDs, duplicate `(id,version)`, invalid answer keys, unresolved source clearances for reproduced material, and SQL tasks lacking passing reference/expected-result tests. It does **not** require any enabled rules at S0; therefore zero enabled rules may structurally pass, but that is NOT a content-complete claim. Add `--stage S1` (minimum 2 complete patterns + 12 reviewed MCQs + 2 lessons + 1 checked SQL task) and `--stage S4` (lean MVP counts ≥30/≥6/≥6/≥3) as **explicit, separate stage gates**. CI always runs `--strict`, and runs the latest successfully completed stage gate; an in-progress stage must run its new gate before being marked done. The default `--review-policy human` retains the human-only gate. An explicit `--review-policy learner` uses the same minima and counts both eligible human-reviewed material and `ai_verified` originals. The validator reports both cohorts and the combined totals. An enabled definition counts toward the human-only gate only if its remediation lesson, detectors and checkpoints also have human review. Detector pools: canonical question `pool` is one of `diagnostic|practice|checkpoint|pre_test_a|post_test_b`; `detector` is a question role indicated by wrong-option misconception mappings, **not a pool**. A checkpoint is reserved from regular/diagnostic allocation. Held-out A/B pools never update training mastery during evaluation.

**Tests:** two distinct wrong distractor signals trigger active status; one signal does not; unrelated wrong answers do not trigger; two distinct clean checkpoints can resolve; same question repeated does not inflate evidence; SQL heuristic is conservative; all remediation content has approved sources; recommendations change when misconception is resolved.

---

## 7. Adaptive decision policy

Pure Python function accepting `mastery`, confidence, evidence coverage, prerequisite graph, active misconceptions, available lessons/questions, recent activities, user goal/time and question exposure history. Returns a typed `NextAction` with `action_type`, `subtopic_id`, optional misconception/lesson/question ID, difficulty, `reason_code`, readable `reason`, `policy_version`.

**Action types:** `DIAGNOSTIC`, `LEARN`, `RETEACH`, `MISCONCEPTION_REMEDIATION`, `PRACTICE_EASY`, `PRACTICE_MEDIUM`, `PRACTICE_HARD`, `SQL_PRACTICE`, `MIXED_REVIEW`, `REVIEW_LATER`, `COMPLETE`.

**Policy v1 order** (available approved material is an invariant for every branch):
1. If a **supported active misconception** has usable reviewed remediation + learner-unseen checkpoints, prefer that remediation, except when a genuinely necessary prerequisite needs attention first; learner may override.
2. For the learner's selected goal/topic, probe insufficient/unknown evidence with a short, distinct domain/subtopic diagnostic. Never force completion of all seven domains before giving remediation.
3. Handle a weak prerequisite when required, then choose weak or review-due available content.
4. Score exactly `≤ 0.40` → teach/reteach + easy practice; `0.40 < score < 0.70` → targeted medium; `≥ 0.70` **with sufficient distinct confidence evidence** → harder/mixed. Unknown or low-confidence score → probe/practice, never declare mastery from one answer.
5. Prefer SQL practice for weak practical SQL competency when safe reviewed tasks exist. Exclude recently seen questions and reserve checkpoint and held-out pools.
6. If the question bank is exhausted, transparently offer review of repeated questions (not new independent evidence). Return `COMPLETE` or alternate-topic suggestion when no eligible work exists; never a dead button.

**Review schedule:** `review_due_at` is separate from mastery score. A successful, independent review moves interval through a simple configurable `[1, 3, 7, 14]` day ladder; a failed review resets interval to 1 day and records a wrong-answer evidence update. No silent mastery decay in v1. No push notifications or background tasks required. Time zones and review date rounding have tests; exposed/repeated questions are not treated as fresh independent evidence.

**Must be explainable:** Do not print a percentage without contextualizing confidence; use reasons like "Two different questions suggest confusion between INNER and LEFT JOIN; try a contrasting example." Log the action and whether the user followed or skipped it.

**User autonomy:** Learner can choose another lesson/question at any time; adaptive suggestions are recommendations, not locks. A user-initiated topic choice still records evidence and can update mastery.

---

## 8. Assessment engine + SQL Lab

### MCQs
- Canonical question `pool`: `diagnostic | practice | checkpoint | pre_test_a | post_test_b` (exact enum). A *detector* is an optional semantic role established by a wrong option's misconception mapping; it is not a sixth pool. Approved detector questions may live in `practice` or `diagnostic`. `checkpoint` questions are reserved and must be unseen by that learner; `pre_test_a`/`post_test_b` are held out from training/practice.
- Exactly 4 options, exactly 1 correct, stable logical ID + immutable integer version, reviewed answer explanation, difficulty, subtopic, source/provenance and review metadata. Never expose correct option, misconception mappings, hidden fixtures, expected SQL/reference query or held-out answers in learner-facing DTOs before authorized grading.
- Resumable five-question sessions, server-side allocations referencing exact question versions. One submission per **session item**, not simply per logical question across all time. Retry same idempotency key + same payload returns stored result; same key + different payload returns conflict. Repeated attempts across independent practice sessions can be logged, but do not inflate independent evidence/confidence.
- Explicitly distinguish `Run` (SQL preview, no mastery change) from `Submit` (graded attempt, single committed evidence update). Record hint exposure before answer. Separate diagnostic versus practice evidence and never update training mastery from held-out forms during experiments.

### SQL Lab
- Start with **SELECT-only SQLite dialect**. Validate the actual SQLite runtime version and record dialect/features per task; SQLite `RIGHT` and `FULL OUTER JOIN` require version ≥3.39.0, while PostgreSQL textbook syntax is not automatically supported.
- Each exercise: statement, schema/columns, seed dataset, expected schema, reference SELECT, validation fixtures (including edge-case datasets when relevant), result-comparison policy (order-sensitive iff specified, duplicate-sensitive by default), difficulty, subtopic, approved misconceptions, hints and source reference.
- Use a **separate killable worker process** and disposable exercise DB fixture, never the application DB; copy/build the fixture first, then open learner connection via SQLite URI `mode=ro&immutable=1` **only when the fixture is truly immutable for the connection lifetime**. Enforce a single supported SELECT (or WITH ... SELECT after parser validation); `sqlite3` authorizer denies writes/schema/ATTACH/PRAGMA/extensions; disable loadable extensions; use `Connection.setlimit()` for SQL/string/blob-related limits (check available SQLite/Python build), progress handler, result row/byte caps, and parent wall-clock kill timeout. Explicitly test huge `zeroblob`/`randomblob`, recursive CTEs, join explosions and memory/resource exhaustion. Unix worker uses OS resource limits where available; Python `resource` is not available on Windows, so implement/test a Windows Job Object equivalent or document **Windows SQL worker untrusted-code hardening unsupported**; do not market unsafe Windows/public deployment. No app secrets/path passed to worker; no arbitrary filesystem/network access. Test at least macOS/Linux local execution before promising cross-platform safety.
- `Run` executes on illustrative fixture; `Submit` grades against hidden alternate fixture(s) and compares result sets; learner receives useful counterexamples but not all hidden expected outputs before a valid submission. Compare with column/order semantics specified by exercise, using multiset comparison when order is irrelevant. Catch SQL errors gracefully; no negative grade due solely to harmless syntactic alternative yielding equivalent data.
- Support stable task versions and save attempted SQL securely. Incorrect SELECT syntax is an *error category*, not automatically a conceptual misconception.
- SQL competency is a separate evidence type, mapped to same subtopic learner model with clear logging; deterministic result grading only.

**SQL worker trust boundary:** A parser is a convenience filter, not the sandbox. Enforce SQLite's authorizer with an allowlist of fixture tables/columns and approved SQL functions. Explicitly deny `load_extension`, schema reads, arbitrary PRAGMAs, ATTACH, and memory-amplifying functions such as `zeroblob` and `randomblob`; also bound SQL expression/statement length and worker process resource use. Resource limits are platform-dependent; if a platform cannot satisfy the adversarial tests, disable untrusted SQL execution there and document the restriction rather than claiming general safety. This local educational defense is not certified isolation for arbitrary internet users.

**Submission/atomicity boundary:** The SQL worker validates a fixed `sql_exercise_version` and fixture hashes and returns a deterministic grade **outside** any app DB write transaction. Then a short `BEGIN IMMEDIATE` transaction rechecks learner ownership, active session-item version, idempotency key + request fingerprint and first-submission uniqueness; it appends attempt, mastery history, misconception evidence, policy decision and recommendation, and commits one stored result. Concurrent duplicate requests may execute worker twice but **must commit at most one attempt/evidence update**. Retry returns the stored outcome; conflicting payload for the same key fails with 409. MCQ grading is cheap enough to happen during this short transaction. No LLM or worker call while the write lock is held.

**Security test suite:** `DROP`, `UPDATE`, `DELETE`, `INSERT`, `ATTACH`, `PRAGMA`, multi-statement, recursive/expensive CTE, `zeroblob`/`randomblob` memory bombs, huge joins, very large result, SQL comment tricks, malformed text and timeout all fail safely; application DB never changes; tests for grading equivalent SQL solutions and duplicate rows.

---

## 9. Backend data model (logical; implement migrations as needed)

Use SQLite FK enforcement, SQLAlchemy 2.x/Alembic, WAL where appropriate and explicit unique indexes. Avoid creating pilot/cache tables before needed. Exact field names may be refined **once** in `docs/api.md`/migrations before implementation, but invariants below must remain intact.

- `users(id, email_unique, password_hash, is_demo, created_at, disabled_at)`, `sessions(id, user_id, token_hash, expires_at, revoked_at)`, `profiles(user_id, goal, level, daily_minutes, consent_at)`. Until S4, the demo-only flow binds dev loopback requests to **isolated synthetic learner identities in a dedicated demo database**, never accepts arbitrary `user_id` from a public request. S4 introduces real login and privacy controls. Never expose an unauthenticated multi-user installation.
- `topics(id, domain_slug, slug, title, description, position)` and `topic_prerequisites(topic_id, prerequisite_id)`. Seven high-level catalog domains, with honest available content per subtopic. CI rejects cycles.
- `lessons(id, subtopic_id)` + `lesson_versions(id, lesson_id, version, body_markdown, review_status, source_ref, reviewed_by, reviewed_at, content_hash)`, UNIQUE `(lesson_id,version)`. Published versions immutable.
- `books(id, source_id, title, original_url, license_notice, default_import_policy)`; `source_section_clearances(id, book_id, section_url, license_url, rights_status, exceptions, reviewer, reviewed_at, accessed_on, approved_content_hash)`; `book_chunks(id, clearance_id, subtopic_id, section, anchor, content, content_hash, import_batch_id)` plus FTS5. **No stored authoritative indexed count**: derive cleared sections from manifest records, indexed sections from committed searchable chunks/import records, and indexed books as the distinct set of books with ≥1 valid indexed section. A clearance alone never increments an indexed count; failed import is atomic and leaves the count unchanged.
- `questions(id, subtopic_id, type)` + `question_versions(id, question_id, version, pool, stem, difficulty, explanation, review_status, source_ref, approved_at, content_hash)` with `UNIQUE(question_id,version)`; `question_options(id, question_version_id, option_index, body, is_correct, misconception_code_nullable)`. Published question versions and their options immutable; at most one misconception mapping per wrong option, exactly one correct MCQ option. `type=sql` version links to `sql_exercise_versions(question_version_id, dialect, fixture_version, expected_result_spec, reference_query, comparison_spec, limits)`, immutable reviewed fixtures.
- `assessment_sessions(id, user_id, kind, status, created_at, completed_at)` and `assessment_session_items(id, session_id, question_version_id, position, status)`; UNIQUE `(session_id,position)`. `attempts(id, user_id, session_item_id, question_version_id, request_idempotency_key, request_fingerprint, result_json, selected_option_id, submitted_sql, correct, hint_used, context, created_at)`; `UNIQUE(user_id,request_idempotency_key)` and `UNIQUE(session_item_id)` for first committed submit. A later practice session may repeat the same question but cannot inflate *distinct question* confidence or misconception independence.
- `mastery(user_id, subtopic_id, model_name, score, confidence_level, attempts_count, distinct_question_count, review_due_at, review_interval_step, updated_at)` with `UNIQUE(user_id,subtopic_id,model_name)`; `mastery_history(id,user_id,subtopic_id,attempt_id,old_score,new_score,model_version,created_at)`.
- `misconceptions(code,subtopic_id,title,rule_version,review_status,enabled,remediation_lesson_version_id)`; `misconception_evidence(id,user_id,code,attempt_id,question_id,question_version_id,evidence_type,reason,created_at)`; `user_misconceptions(user_id,code,state,evidence_count,last_seen_at,resolved_at)` with unique `(user_id,code)`. User `state` and definition `review_status` are never conflated.
- `policy_decisions(id,user_id,trigger_attempt_id,policy_version,model_version,input_snapshot_json,selected_action,reason_code,created_at)` and `recommendations(id,user_id,policy_decision_id,action_type,subtopic_id,reason,created_at,followed_at,skipped_at)`. Policy inputs are bounded/redacted snapshots sufficient to reproduce decisions; optional generic event log must not duplicate decisions.
- Auth, tutor message/source tables and research consent tables are introduced at their stages. Explanation cache, BKT/Elo and pilot tables are deferred.

**Atomicity:** SQL results are computed in the worker outside write transactions, then committed with the version-locked attempt and state updates in one short immediate transaction; see §8. Idempotency requires unchanged response on a retry and 409 on same-key different payload. No SQL worker/LLM inside a write transaction.

**Demo-data safety:** `scripts/reset_demo.py`, `seed_demo.py`, `verify_demo.py` **MUST** use a dedicated `data/demo.sqlite` or temp-path database, explicitly refuse to operate on configured production/regular app DB or outside an allowlisted demo path, and never remove non-demo users' records. The end-to-end replay is part of stage-boundary verification. Test this with a separate non-demo DB checksum. Bind demo API to loopback-only until proper auth exists.

**Privacy:** By S4 provide tested `/me/export` and `/me/delete` for authenticated users, with explicit policy for retaining genuinely deidentified experimental data only where consent permits. Redact tokens, emails and raw learner SQL from logs. Never trust client-supplied user IDs. Human-study participation requires explicit consent and guide/institution approval where applicable.

---

## 10. API contracts — implement with typed Pydantic DTOs

Base `/api/v1`; OpenAPI docs available locally. Health is precisely `GET /api/v1/health` (not `/health`). Endpoints below describe required functionality; exact naming can be refined in `docs/api.md` before implementation, then frozen. Every auth-sensitive endpoint uses server-resolved user IDs, never trusts client `user_id`.

| Endpoint | Purpose / response |
|---|---|
| `GET /api/v1/health` | DB/app readiness (all routes under `/api/v1` except framework docs) |
| `POST /auth/register`, `/auth/login`, `/auth/logout` | Local accounts and sessions |
| `GET /me`, `PATCH /me`, `GET /me/export`, `DELETE /me` | Profile/privacy |
| `GET /curriculum` | Domains, subtopics, prerequisites, topic availability |
| `GET /lessons/{id}` | Approved curated lesson and linked sources |
| `GET /library/books` | Five source catalog records with rights/index status |
| `GET /library/search?q=&topic=` | FTS source hits and attribution |
| `POST /assessments/start` | Allocate diagnostic or study assessment, no answer keys |
| `POST /assessments/{id}/submit` | Idempotent deterministic grading and appropriate evidence updates |
| `POST /practice/sessions` | Create/resume 5-question practice session |
| `GET /practice/sessions/{id}` | Current question and progress, no key |
| `POST /practice/sessions/{id}/answer` | Grade, store, mastery delta, misconception evidence, next action |
| `GET /recommendations/next` | NextAction including human-readable why |
| `GET /progress` | Mastery with confidence, coverage, attempts, history |
| `GET /misconceptions` | Evidence-based possible/active/improving/resolved hypotheses |
| `GET /sql/exercises/{id}` | Schema, prompt, dialect and public sample rows |
| `POST /sql/exercises/{id}/run` | Bounded execution result on visible dataset |
| `POST /sql/exercises/{id}/submit` | Hidden-fixture grade, feedback and evidence update |
| `POST /tutor/explain`, `/tutor/ask`, `/tutor/hint` | Grounded tutoring with source metadata and `degraded` flag |

**Response guarantees:** consistent `{detail, code}` for errors; all mutating attempts accept an idempotency key; hide reference SQL and hidden fixtures from learner DTOs; no unsafe direct table exposure. Provide sample JSON requests/responses and generated client types. Use a pagination or limit scheme for history/library results.

---

## 11. Repository layout

```text
adaptive-dbms/
├── AGENTS.md                   # concise Codex working rules
├── MASTER_PLAN.md             # v1.2; only project plan
├── DECISIONS.md               # deadline/review assumptions, decisions + blockers
├── README.md
├── .env.example
├── .gitignore
├── frontend/
│   ├── src/
│   │   ├── app/               # router, query client, auth shell
│   │   ├── pages/             # dashboard, learn, library, practice, sql, progress
│   │   ├── features/          # isolated feature components/hooks
│   │   ├── components/        # common accessible UI
│   │   ├── api/               # typed API client
│   │   └── test/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # config, DB, auth, errors
│   │   ├── db/models/         # SQLAlchemy entities
│   │   ├── api/               # thin FastAPI routers
│   │   ├── schemas/           # Pydantic DTOs
│   │   ├── services/
│   │   │   ├── assessment.py
│   │   │   ├── mastery.py
│   │   │   ├── adaptive.py
│   │   │   ├── misconceptions.py
│   │   │   ├── curriculum.py
│   │   │   ├── retrieval.py
│   │   │   ├── tutor.py
│   │   │   └── sql_grading.py
│   │   ├── providers/         # curated, ollama
│   │   └── sql_worker/        # isolated execution process
│   ├── migrations/            # Alembic
│   ├── tests/                 # unit / integration / adversarial
│   └── pyproject.toml
├── content/
│   ├── manifests/books.yaml  # verified licenses, access dates, section exceptions
│   ├── curriculum/topics.yaml
│   ├── curriculum/prerequisites.yaml
│   ├── lessons/
│   ├── questions/             # draft and reviewed pools, immutable versions
│   ├── misconceptions.yaml
│   └── sql_fixtures/
├── scripts/                    # validate_content.py, import_books.py, seed_demo.py, verify_demo.py, reset_demo.py
├── experiments/                # pre/post, retrieval, models, results when ready
├── data/                       # demo.sqlite and app databases (ignored by Git)
├── docs/                       # stage_tasks_S0_S1.md, content_authoring_guide.md, rights_clearance_workflow.md, architecture, API
└── .github/workflows/ci.yml
```

No duplicate architecture plans or old version files are kept in the repository root. All business rules live in pure/testable services. Routers must be thin. Book imports run as scripts, not in HTTP requests. SQL executor launches independently and is never given app DB path or secrets. No abstract classes/frameworks merely for aesthetics; interfaces exist only where swapping providers/models/policies is valuable.

---

## 12. Revised execution — build the distinctive learning loop first

**Stages S0–S6 replace the former M0–M12 sequence; do not execute the old order.** Code agents must split each stage into small, reviewable tasks, writing the tests and acceptance criteria *before* committing. Update `IMPLEMENTATION_STATUS.md` after every passing task. Keep one known-good seeded demo that is rerun after each stage. A stage is complete only when its exit tests actually pass, not when scaffolding exists.

### S0 — Source of truth, constraints, content and app skeleton [MUST]
- Place this document in repo root as `MASTER_PLAN.md`, with `AGENTS.md`, `DECISIONS.md`, `IMPLEMENTATION_STATUS.md`, `docs/stage_tasks_S0_S1.md`, `docs/content_authoring_guide.md`, `docs/rights_clearance_workflow.md`, and `content/manifests/books.yaml` at exactly these paths. Archive obsolete local plans outside the active repo **without deleting unrelated user work**. Supporting docs operationalize this plan, never override it.
- Log unknown submission date, available hours, review capacity and platform in `DECISIONS.md`; default to lean solo scope without pretending to know actual constraints.
- Create content schemas and `scripts/validate_content.py`; implement structural `--strict` checks first, then `--stage S1/S4` gates. Author/AI-draft the two initial misconception patterns, questions, lessons and SQL JOIN task; **draft is not approved**.
- Scaffold React/Vite/Tailwind, FastAPI/SQLite, migration/test/CI, `/api/v1/health`, one shell page and a dedicated demo DB path. CI runs strict structural validator even if content is not yet approved.
- **Exit:** apps start from clean documented commands; no paid accounts/secrets; preliminary YAML validates; all user data is untouched; one master plan.

### S1 — Walking skeleton: full learning loop in browser [MUST, EARLY]
- Implement versioned question/lesson tables and real immutable content allocation; deterministic MCQ grading and one restricted SQL LEFT JOIN worker/grader with hidden fixtures, adversarial tests and explicit platform limits.
- Implement baseline mastery, distinct-evidence misconception states, minimal explainable policy, stored decision and atomic/idempotent attempt command; verify score boundaries and concurrency.
- Provide a **minimal browser demo screen**, not just CLI, for learner A/B switching in a dedicated local-demo DB: answer → feedback → approved lesson → unseen checkpoints → changed recommendation, plus SQL task submission. Do not deploy the unauthenticated demo endpoint publicly.
- Verify enough content for `validate_content.py --strict --stage S1 --review-policy learner`: two complete patterns, ≥12 reviewed MCQs including ≥4 ordinary practice, ≥2 reviewed lessons, ≥1 independently result-checked SQL JOIN task. Record human-only coverage separately. Provide deterministic `reset_demo.py`, `seed_demo.py`, `verify_demo.py`. Reset refuses the app DB.
- **Exit:** minimal browser flow and integration tests pass, demo CLI verifies both learners, SQL worker adversarial tests pass, and `--stage S1 --review-policy learner` passes using the original reviewed bank. Retain and report the distinct human-only gate.

### S2 — Adaptive intelligence + robust practice [MUST]
- Develop pure mastery and policy services with confidence/coverage, independent evidence, review-due scheduling, prerequisite checks, question exposure, idempotent atomic attempts, stored policy decisions and rationale.
- Build resumable five-question sessions and topic-level screening followed by optional subtopic probes; no false certainty about dozens of subtopics.
- Enforce the content-done gate in CI for every `enabled=true` approved misconception definition. Add strict learning correctness, deterministic recommendations and no-content fallbacks.
- **Exit:** two learners with different evidence get different explainable next actions; same question replay doesn't inflate confidence; crossing score thresholds is simulated and tested; demo re-run passes.

### S3 — Grounded library and tutoring foundation [MUST]
- Perform section-level rights audits; import **two actually approved and indexed sources**, aiming for appropriate portions of BCcampus and Runestone but **skip BCcampus Chapters 10 and 11 until its exception is separately cleared**. If a source cannot pass audit, keep it link-only and substitute a correctly licensed source/section rather than inventing rights.
- Build idempotent import, FTS5/BM25 retrieval over approved lessons and individually cleared book sections, citations with section anchors, source status labels, curated explaining/simplifying/hint responses and a provider contract tested with a mock. A clearly labeled authored lesson fallback must work when retrieval fails.
- **Exit:** target two actually cleared sources searchable; if rights clearance blocks this, explicitly record a source-count shortfall and ship only the genuinely indexed content plus authored fallback. No false claim of two sources or passing the two-source target; technical S3 features may be accepted with a documented rights blocker. Demo still passes.

### S4 — A polished usable tutor and privacy controls [MUST]
- Add password/session authentication and strict same-origin mutation-header protection; profile/onboarding, dashboard, Learn, Practice, SQL Lab, Library, Progress, Ask Tutor, and tested `/me/export` plus `/me/delete`; remove dead controls and add empty/loading/error states.
- Complete a realistic small content bank: target ≥30 publication-eligible MCQs, ≥6 real SQL exercises, ≥6 lessons, ≥3 fully supplied misconception patterns; do not enable empty modules. 7-domain navigation remains visible, with undercovered areas labeled.
- Harden SQL worker with execution limits and adversarial tests; add editor, fixture examples, hidden grading fixtures, duplicate-aware output comparison and dialect/version labels.
- **Exit:** clean sign-in → screen → lesson → practice → remediation → SQL lab → progress works and persists for two separated users; account export/delete and auth/CSRF protection are tested; automated seeded demo and `--stage S4 --review-policy learner` pass. Report the separate human-only gate.

### S5 — Ollama tutoring, hardening and evaluation [MUST core / OPTIONAL extras]
- **Must:** further adversarial testing of `/me/export` and `/me/delete` already shipped in S4; authentication/CSRF/user-isolation tests; resilient source import and worker security tests; accessibility, error handling, migration check, reproducible scripts; CI and documented known limitations.
- **Must for final-year academic quality:** offline retrieval hit@k with a labeled query set (record whether only author-reviewed or independently reviewed); synthetic policy simulations explicitly labeled **synthetic**; reproducible metrics and content quality review. Never infer actual learning gains from simulations.
- **Must:** Integrate Ollama with `qwen3:1.7b`, bounded follow-up history, learner-specific context, progressive hints, SQL mistake explanations, evidence-backed citations and curated fallback. Verify provider failures with mocks, and run an opt-in real-model check on the target machine.
- **Optional:** Explanation cache only if needed; expansion to ≥80 MCQs/≥20 SQL exercises/≥6 complete misconceptions, glossary, chapter navigation, prerequisite graph page and BKT/Elo only after core proof and content review capacity.
- **Conditional pilot:** faculty approval and consent, matched fixed/adaptive exposure, held-out assessments; describe small samples (e.g. 10–30) as **feasibility**, not efficacy, and use crossover only when carryover is addressed.
- **Exit:** no fabricated data/claims; tests passing; real-model check passes on an 8 GB development machine or equivalent, curated fallback is verified, and demo reset/replay passes.

### S6 — Submission, reproducible demo and viva [MUST]
- Final README, system architecture, ER diagram, migrations and schema dictionary, API contracts, security model, approved content counts, source licenses/section exceptions, limitations, evaluations and viva Q&A.
- `scripts/reset_demo.py && scripts/seed_demo.py && scripts/verify_demo.py` must run deterministically from a clean local setup. Demo includes learner A/B contrast, independent misconception evidence, contrasting remedial lesson, unseen checkpoints, changed recommendation and restricted SQL execution.
- Record exact tested OS, Python/SQLite versions, test outputs, installation steps, any missing book-index count, and what remains future work.
- **Exit:** another person can clone, start and follow one scripted 5–10-minute demo with no paid dependencies or Internet-based AI; no manual database surgery.

**Cuts when the real deadline is short:** keep the S0–S6 core. If book audits block imports, run retrieval over eligible original lessons and keep uncleared books as catalog links. Reduce content breadth, optional extras and research comparisons first. Never cut safe SQL isolation, deterministic grading, rights gates, or content review. **Content targets unlock only after reviewed capacity is established**, not because an agent can generate large YAML files.

**Codex task granularity:** For each stage create 3–8 small tasks. Each task states files touched, a single demonstrable behavior, tests run, expected output, content/right blockers, and a commit. Update `IMPLEMENTATION_STATUS.md` after green tests; run `validate_content.py --strict`, the relevant `--stage` gate and `verify_demo.py` at each stage boundary. Never call an unexecuted test passed.

---

## 13. Tests that must exist before claiming "done"

### Unit
- Mastery bounded and monotonic for correct/incorrect evidence; explicit tests for `0.5 → 0.4`, `0.5 → 0.6 → 0.68 → 0.744`, inclusive threshold boundaries; confidence based on distinct questions; repeated/idempotent attempt unchanged; review-due interval independent from mastery.
- Policy thresholds, prerequisites, unknown topic coverage, no-content fallback, question exhaustion, learner override, misconception priority and reasons.
- MCQ scoring, wrong distractor hypothesis mapping, evidence independence, resolution checkpoints, controlled SQL result equivalence; failed `validate_content.py --strict` for enabled pattern missing any detector/lesson/checkpoints; immutable version references.

### Integration
- Synthetic learner A/B demo → diagnostic probe → lesson → practice → grade → misconception evidence/checkpoints → mastery history → changed recommendation; once auth exists, repeat under signed-in session.
- Same user refresh/resume; multi-user isolation; duplicate submission rejected; hidden answer keys never leaked.
- Section-cleared source import → FTS search → passage metadata → answer citations; BCcampus Chapters 10 and 11 cannot be imported as blanket CC BY; unavailable LLM returns curated content. Mock-provider integration covers grounded follow-ups, hint progression, SQL feedback and timeout/busy fallback. A separate opt-in integration check demonstrates real local inference with the installed model.
- SQL practice with valid/invalid queries, blob-memory bomb, long-running query and malicious write attempt; compare hidden fixtures; confirm application DB unchanged and killable worker resource bounds.

### End-to-end / acceptance
- Learner A and learner B produce different recommendations from different outcomes.
- Two different wrong questions flag an active misconception and remediation; two independent correctly answered checks resolve or reduce it.
- Learner can finish a task with keyboard only; form labels, contrast and error states checked.
- Five **catalog** sources visible with accurate indexed/licensing and section-exception status; no false claim that link-only books were indexed; re-run seeded demo after every stage.

### Quality measures
- Run frontend build, typecheck and lint; backend tests/lint; real migration check; API schema generation.
- Track pass/fail in `docs/test-report.md` with date/version. Never mark a test "passed" without execution. CI must enforce content gate and reject drafts/uncleared source content in production seeds.

---

## 14. Research integrity and educational validity

**The academic claim is a question, not a conclusion:** "Can a learner-state-driven adaptive DBMS tutor improve conceptual learning and SQL task performance versus a matched fixed path?" A working app proves engineering feasibility, not educational effectiveness.

**Recommended evaluation:** Treat a likely small student cohort as a **feasibility pilot**, not a powered learning-gain comparison. If conducted, use matched question pools, lessons, time budgets and tutor access; only next-action policy differs. Prefer within-person or counterbalanced crossover where appropriate, but account for carryover/learning effects and pre-register outcomes when possible. Test forms A/B held out from practice, counterbalanced if possible. Report absolute score change and uncertainty; explicitly handle ceiling scores for normalized gain. Sample sizes and exposure times recorded; do not claim statistical significance without a valid analysis.

**Model evaluation:** For enough real sequential attempt data, predict before each response, fit on training users, evaluate on held-out users; report log loss/Brier/calibration and sample size; compare simple baselines. If insufficient data, skip model superiority claims. Simulated learners assess code/policy under assumptions, not actual educational outcomes.

**Retrieval evaluation:** Reviewer-approved query set with expected supporting sections; compute hit@k/MRR, test source citation correctness and human-rated answer faithfulness. Compare FTS5 to optional embeddings using same queries, then choose. Include unanswered questions and retrieval failures.

**Content quality:** Record reviewer identities/status (including unavailable independent review), enforce content-coverage CI, verify SQL answer keys with actual execution across hidden datasets, and maintain approvals for MCQs, SQL fixtures, misconceptions and lessons; preserve source attribution and versioning; separate generation draft from approved material. Do not put fabricated author names, chapter numbers or passages in a submitted report.

---

## 15. Source/technology reference URLs (book license observations checked 2026-11-22; re-check before importing)

- BCcampus DB Design: https://opentextbc.ca/dbdesign01/
- Runestone Practical DB: https://runestone.academy/ns/books/published/practical_db/index.html
- DataField database book: https://datafield.dev/sql/
- Brendan Shea SQL book: https://brendanpshea.github.io/database_sql/
- OpenStax Information Systems: https://openstax.org/books/foundations-information-systems/
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- SQLite FTS5: https://www.sqlite.org/fts5.html
- SQLite authorizer/progress handlers: https://docs.python.org/3/library/sqlite3.html
- Ollama: https://ollama.com/

**Legal note:** Publisher-level license notices above are verified as of 2026-11-22, but all chapters, images, datasets, examples and third-party materials are **not** cleared by that alone. BCcampus Chapter 10 has a CC BY 3.0 derivative attribution. Chapter 11 has a CC BY-SA 3.0 derivative attribution. Runestone cover art, OpenStax credited artwork and Shea third-party media require their own review. DataField Chapter 26 has exact excerpt evidence as recorded in §4. NC works are not automatically permitted in a commercial derivative/distribution. No legal claims are made beyond the identified primary notices.

---

## 16. Codex operating rules (copy a concise version to `AGENTS.md`)

1. Read only **`MASTER_PLAN.md` v1.2** as project design authority; do not follow the superseded v1.0, `PLAN.md`, `PLAN_PHASE2.md` or outside critique notes. Rights and approved-content YAML are data inputs, not alternate architecture plans.
2. Start with S0, then S1 and subsequent stages. Before each small task, specify touched modules, expected behavior and acceptance tests. Do not build seven empty screens before a working learning loop.
3. Record actual deadline/review capacity as unknown until given; default lean solo scope, not invented submission dates. Do not block foundation work to ask for details already explicitly resolved.
4. Content authoring begins at S0; no LLM-written answer key can approve itself. Every active misconception must pass content-done gate; drafts cannot silently appear in production pools.
5. Never import a section without recorded per-section rights clearance. Keep OpenStax link-only pending written permission and BCcampus Chapters 10 and 11 pending separate review; do not infer rights from free access. Maintain exact number indexed in UI.
6. No paid services, required cloud accounts or Docker; required Ollama tutoring must degrade gracefully. Student SQL is executed only in restricted, independently tested subprocess/fixtures; no direct app-DB execution.
7. Persistent seeded A/B demo is a first-class CI/regression artifact from S1 onward. Run reset → seed → verify after every stage, and every migration that could affect attempts/policy.
8. Grade and update deterministic learning state; LLM cannot change score, question answers, misconception state or policy. Keep question versions and policy decisions immutable/auditable.
9. Commit each passing task; update `IMPLEMENTATION_STATUS.md` and `DECISIONS.md` with test results, blockers and next action. Never call untested or incomplete work complete.
10. Start now by scaffolding and validating initial content/rights manifest; when the first runnable feature is ready, build the end-to-end A/B misconception and SQL challenge rather than more infrastructure.

---

## 17. Final acceptance — lean core, transparent expansion

- [ ] One consistent **v1.2** plan in the repository; no conflicting active old plans.
- [ ] Runs locally and without paid API, external AI, Docker or hosted DB; documented tested platforms.
- [ ] Friendly, coherent, accessible learning UX with real content and no dead links/buttons.
- [ ] Five catalog sources with verified book notices and dated rights manifest; **real** indexed count, section-level approval and exceptions (especially BCcampus Chapters 10 and 11).
- [ ] A complete working two-learner demo: independent error evidence → possible/active misconception → curated explanation → unseen checkpoints → persisted mastery/recommendation change.
- [ ] ≥30 publication-eligible MCQs, ≥6 executable SQL tasks, ≥6 lessons and ≥3 fully covered misconception patterns **for the default lean scope**; human-only coverage and unmet stretch targets reported separately.
- [ ] Content-done validator fails CI for missing detector coverage, lesson, unseen checkpoints, source rights or answer verification.
- [ ] Safe isolated SQL grading with hidden datasets, SQLite runtime-specific dialect tags, timeouts, blob/resource limits and hostile-input tests; never expose app DB to student queries.
- [ ] Deterministic grading, immutable question versions, idempotent attempts, explainable policy snapshots, independent evidence and review-due scheduling without unvalidated score decay.
- [ ] Ollama with `qwen3:1.7b` demonstrates personalized, source-grounded tutoring and follow-ups on the target hardware. Curated tutoring works offline. Application-generated citations and deterministic assessment retain their authority.
- [ ] Authenticated multi-user separation (by S4), predictable sessions, secure mutation origin checks, export/delete, adequate tests and documented deployment limitations.
- [ ] Reproducible evaluation of retrieval and policy behavior, no claim of proven learning benefit without adequate human evidence.
- [ ] Demo seed/reset/verify scripts pass after every stage; fresh clone demo and final viva materials are usable and honest.

**Guiding principle:** one excellent, repeatable, content-complete intelligent DBMS tutoring loop beats seven half-empty topics, five falsely indexed books, or a superficially impressive AI chatbot.

---
