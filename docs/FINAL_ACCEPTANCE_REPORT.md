# Adaptive DBMS Tutor final acceptance audit

- Audit date **23 November 2026**
- Starting revision `9a9aed59cbc4e9518e64d1c4c40dce1cca6b11cc`
- Audited product revision with fixes `3b56e5c5be1edf2e0fd4f5c647f37afd9dc2881a`

## 1. Executive decision

| Intended use | Decision | Evidence and boundary |
|---|---|---|
| Local final-year college demonstration | **CONDITIONAL GO** | The real learner journeys, authored A/B demo, SQL grading and grounded Ollama tutoring passed on the Apple Silicon Mac. Demonstrate the lean bank and disclose the content, model and assessment limits below. |
| Public deployment | **NO-GO** | The SQL restrictions and account controls were tested for a loopback installation. Public multi-tenant isolation, hosted security, TLS configuration and capacity have not been established. The demo endpoints are for local use. |
| Human study or high-stakes assessment | **NO-GO** | The human-only S1 and S4 gates each have zero qualifying items. The app has no approved human study, independent human sign-off on an assessment bank, validated held-out forms, or real learning-outcome evidence. |

I used the real React frontend, FastAPI backend, installed Ollama and newly migrated SQLite databases in a disposable checkout of the starting revision. The demo reset targeted only that checkout's allowlisted synthetic DB. Tests used installed Google Chrome through Playwright, separate browser contexts and invented accounts. I restored the ordinary local application with its existing data after the audit.

## 2. Feature checklist against the master plan

Statuses refer to the audited revision. **PASS** means direct browser, runtime or regression evidence. **PARTIAL** means an implemented surface has a specific limit. **FAIL** means an applicable gate reproduced a failure. **NOT TESTED** marks an unverified environment or claim.

| Major feature | Status | What was established |
|---|---|---|
| Local setup and versioned storage | **PASS** | Fresh Alembic upgrade to `0007_ai_review`, no drift, lesson import and protected demo seed/reset/replay. Separate account and demo databases. Immutable published versions exercised in regression. |
| Registration, login, logout, invalid credentials, persistence | **PASS** | Real Chrome exercised the forms, a bad login and login after sign-out. Reload retained the account and preferences. Browser cookie was HttpOnly and SameSite=Lax. |
| Onboarding and preference effects | **PARTIAL** | Goal, experience and time budget were saved and survived reload. Goal and experience are supplied to the tutor. The activity policy does not rank by all preferences and daily minutes do not constrain recommendations. |
| Dashboard and adaptive recommendations | **PASS** | Observed zero-state diagnostic CTA, readable reasons, different actions after different evidence and a changed action after resolution. Verified loading/error retry. Policy uses performance, prerequisites, availability and exposure. |
| Curriculum and lessons | **PARTIAL** | Seven domains, visible prerequisites, real rendered examples, exact chapter links and topic practice navigation. Substantive material covers keys, foundational SQL, and FDs/normalization. The other areas supply catalog navigation with pending content. |
| Diagnostic and practice | **PARTIAL** | Server-owned diagnostic, five-question practice when inventory permits, reload/resume, targeted selection, feedback and progress. The bank has four diagnostic items over three domains, so coverage is a lean screen. |
| Deterministic MCQ and SQL grading | **PASS** | Reviewed answer explanations followed real attempts. Existing DTO regression withholds keys before grading. SQL graded against hidden results and rejected a query that matched every visible result row yet merged two customers on a hidden fixture. |
| Misconception detection and remediation | **PASS** | Foreign-key and JOIN patterns advanced from one signal to active and resolved after two fresh correct checkpoints. Normalization reached `improving` after a missed checkpoint, and a repeated detector no longer inflated evidence. |
| SQL Lab on Apple Silicon macOS | **PASS** | Chrome showed sample data and a labeled CodeMirror editor. Visible preview, incorrect and correct submission, error feedback, execution budget, grouped counts and NULL behavior were exercised. All six exercises ran against all three fixtures. |
| Grounded tutoring, follow-up and fallback | **PASS** | Real `qwen3:1.7b` explained key multiplicity and LEFT JOIN and answered a contextual follow-up. Chrome showed genuine citations, explicit no-evidence feedback and a curated fallback with an unreachable provider. |
| Hints and SQL mistake explanations | **PASS** | Open practice items now have three distinct curated reasoning steps. A reviewed explanation handles the original count-exercise mismatch. Other eligible tutoring can use the local model with safe post-grade context. |
| Mastery, attempts and revision | **PARTIAL** | Chrome showed topic score, confidence, history, hypotheses and the revision empty state. Regression exercised time-based due and confidence rules. The UI has no study-time tracking or mastery trend chart. A live clock advance to a due date was not run. |
| Settings, data export, deletion and isolation | **PASS** | Downloaded a synthetic account export, verified its ownership and absence of credential fields, signed out and back in, canceled and then completed deletion. Deleted credentials were rejected. A different account's session showed a 404. |
| Library, attribution and book imports | **PARTIAL** | Five source links, rights disclosures, zero indexed books, and search over six independently stored original lessons. Book imports remain blocked by section rights. Synthetic import/revocation and hash checks pass. |
| Seeded authored Learner A/B demo | **PASS** | Both learners and their distinct hypotheses worked in Chrome using actual content. Programmatic replay and reset protections also passed. |
| Keyboard and responsive basics | **PASS** | Main routes and a representative lesson checked at desktop/mobile widths. Keyboard-only Library search, skip link/focus, labels, table names and live statuses inspected in Chrome. |
| Assistive technology and cross-browser coverage | **NOT TESTED** | No VoiceOver, other screen readers, WCAG conformance audit, Safari, Firefox, Android or iOS device tests. |
| Public deployment and portability of untrusted SQL | **NOT TESTED** | No public deployment was attempted. The worker is enabled only on the tested Apple Silicon macOS platform. Linux CI does not exercise that worker's OS restrictions. |
| Human-only and publisher acceptance | **FAIL** | Both human-only gates exited 1 at their original thresholds. The initial target of two indexed books remains unmet. |

**Remaining plan scope.** Expanded 14–21 question screening, denser seven-domain content, publisher chapter navigation, glossary, richer analytics, benchmarked embeddings and BKT/Elo are deferred. A study consent/assignment flow, validated held-out assessment forms and outcome evaluation are missing for research use. Recommendation follow/skip telemetry and a tutor thread history picker are also absent. Tutor messages persist on the server and appear in the export. Reloading the UI starts a new visible thread.

## 3. Chrome journeys and educational evidence

| Learner or workflow | Input, expected outcome and actual observation |
|---|---|
| Student A, beginner | Selected the repeat-reference distractor for tickets and then clubs on separately allocated questions. Expected one cautious signal, then targeted instruction. Chrome showed `possible → active`, recommended **One parent, many child rows**, and delivered a simple model explanation plus a follow-up about a separate uniqueness constraint. Chose the correct office/NULL and booking uniqueness responses on the two unseen items. Observed `resolved`, 56% with emerging confidence, four distinct responses and a recommendation to practice. |
| Student B, intermediate | Selected INNER JOIN for the all-routes report and a NULL-extended row under INNER JOIN. Expected independent JOIN evidence separate from Learner A. The demo showed `SQL-JOIN-01` with one then two signals. The reviewed lesson and real model's follow-up explained South's NULL right-side values. Both checkpoints resolved the hypothesis. During signed-in SQL practice, grouping by customer name produced the expected visible rows and failed hidden grading. Grouping by ID and counting matched order IDs passed. A wrong query produced no automatic misconception. |
| Student C, competent | Answered targeted keys, JOINs and normalization probes correctly. Expected no misconception and modest next guidance given one answer per topic. Observed three correct attempts, no hypothesis, three assessed topics and a practice recommendation to build evidence. Exported only that account's data. |
| Repeat and missed-checkpoint variants | Before the fix, a first wrong detector plus a wrong replay of an earlier correctly answered detector escalated to active. After the fix the same sequence stayed at `possible` with one signal. A distinct normalization sequence activated `NORM-03`. One wrong and one correct checkpoint left it `improving` and returned to general practice when fresh checks ran out. |
| Navigation, privacy and errors | Clicked account, Dashboard, Learn, Practice, SQL Lab, Library, Progress, Settings and Tutor controls. Created and deleted a synthetic account, verified its login failed afterward, and verified private session rejection in another browser context. A delayed progress response showed a loading state. A deliberately failed health request showed an error and Retry restored readiness. |
| Keyboard and selected source links | Tab and Enter moved focus to Main using Skip to content. Typed and submitted Library search using the keyboard. Chrome's accessibility tree exposed a named searchbox and named results region. Source links shown by the FK and JOIN answers matched the actual publishing chapters. |

The bank is useful for the tested concepts and supplies feedback on common errors. It contains 20 practice MCQs (17 ordinary and three mapped detectors), four diagnostic MCQs, six reserved checkpoints, six lessons and six SQL exercises. The small bank naturally repeats items. Fresh independent responses govern confidence and misconception status. A change in the recorded score alone provides limited evidence of learning. Sampled factual checks included nullable child keys, LEFT JOIN preservation, COUNT's treatment of NULL, grouping by identifiers and partial versus transitive dependency. [Educational review](educational-review.md) · [SQLite foreign keys](https://sqlite.org/foreignkeys.html) · [SQLite aggregates](https://sqlite.org/lang_aggfunc.html) · [Runestone joins](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/04-multiple-tables/multiple-tables.html)

## 4. Visual and accessibility findings

Chrome exercised 10 views at 1440 × 900 and 390 × 900 (Dashboard, Learn, Practice, SQL Lab, Library, Progress, Settings, Ask Tutor, Learner Demo and a lesson), plus the signed-out sign-in and registration forms. The baseline candidate-key table widened the 390 px page to 418 px, and the demo showed literal Markdown. The fixed lesson scrolls its long content within the card, the page measured 390 px, and the demo renders a semantic table with the review label. Primary actions and feedback were visually legible. Mobile navigation takes a large part of the first viewport. Chrome's computed colors gave approximately 9.05:1 for the enabled sign-in button label and 7.08:1 for introductory copy. These are spot checks. No formal accessibility conformance result was established.

There were no uncaught JavaScript exceptions in the completed journeys. The console showed expected responses during negative tests (401, 404 and 422), the deliberate network error, and a missing favicon request. Local route and report links were checked. Exact external chapters used during the sampled tutor and lesson journeys were verified. Other external links were outside the browser link pass.

[Desktop demo with rendered remediation](acceptance-screenshots/demo-desktop.jpg) · [Mobile lesson after width fix](acceptance-screenshots/lesson-mobile.jpg) · [SQL feedback and visible sample rows](acceptance-screenshots/sql-feedback-desktop.jpg) · [Library catalog](acceptance-screenshots/library-desktop.jpg)

## 5. Tutor and retrieval results

- **Real model:** On the audited revision, the corpus script and browser returned grounded explanations for LEFT JOIN preservation and NULL-extended right columns. The beginner's follow-up used the same conversation. A request to cite a made-up source returned only the genuine chapter link. One prompt check is a bounded observation, and the model can still give plausible but wrong prose.
- **Teaching guardrails:** Uncontrolled open-item hints repeated a fragment, and the small model twice gave bad advice about counting zero-order customers. Open items now use three deterministic guidance prompts. The known count mismatch cites the reviewed LEFT JOIN lesson and explicitly counts the right-side order ID, keeping zero-order customers. The checked follow-up repeats that reviewed guidance. Other model explanations remain advisory and grading stays application-owned.
- **Fallback:** An audit backend configured with an unused loopback Ollama port returned “Curated explanation · local AI unavailable” with the genuine JOIN lesson. With a made-up out-of-scope search term the normal provider flow showed that reviewed evidence was unavailable and returned no citations.
- **Retrieval:** Six locally indexed original lessons and zero publisher sections. The six draft-labeled evaluation queries all ranked their expected lessons first (hit@4 and MRR both 1.0). This small smoke set gives no general retrieval accuracy or learning-effect estimate. [Rights review package](section-rights-review.md)

## 6. Safety and privacy evidence

- **Authentication and privacy:** Browser tests observed session persistence, rejected credentials and separated accounts. Regression covered expiry, revocation, bounded password checks, cross-account access to sessions and tutor threads, export isolation and cascade deletion. This confirms application-level deletion from the current DB. Secure erasure, backups, machine-level security and HTTPS deployments were outside scope.
- **Mutations and grading:** Regression exercised Origin/Referer rejection, ownership, redacted invalid requests, same-key idempotency, concurrent duplicate commit and rollback. Neither a model reply nor SQL preview writes an authoritative grade. Learner DTOs withhold the key, versioned expected results and hidden SQL fixtures before grading.
- **SQL boundary:** Browser exercised valid SELECTs, syntax/schema failure and a bounded resource error. Worker regression also exercised denied statements, application DB isolation, output caps, worker timeout and reaping, and platform limits. The read-only worker uses a disposable fixture and a blank environment. These are local defense-in-depth checks. They establish no guarantees about a public service, arbitrary OS-level attacks or platforms where the worker is disabled.
- **Model and rights:** The request bounds its prompt/history and uses loopback inference. Application-owned sources survive citation validation. Tests checked model fallback and a fictional source request. General prompt-injection resistance and factual correctness over arbitrary questions remain unestablished. Approved-section hashes and human rights status gate publisher import. No new rights or human sign-off were granted.

## 7. Commands run and results

Environment was Apple Silicon macOS 27.2.1 (26B131), Python 3.12.16, SQLite 3.54.1, Node 26.13.1, Google Chrome 157.0.8103.79 and local `qwen3:1.7b`.

| Check | Observed result |
|---|---|
| `bash scripts/check_backend.sh backend/.venv/bin` | Baseline 130 passed. After fixes, **138 passed** and Ruff, strict mypy and structural validation passed. |
| `npm --prefix frontend run lint`, `run typecheck`, `test`, `run build` | ESLint, TypeScript, **two Vitest tests** and production bundle passed. |
| `DBMS_TEST_CHROME=1 npm --prefix frontend run test:e2e` | Four synthetic Chrome E2E scenarios passed. Two authored-only cases intentionally skipped in this invocation. |
| `DBMS_TEST_CHROME=1 DBMS_TEST_AUTHORED=1 npm --prefix frontend run test:e2e -- authored-demo.spec.ts` | Two authored Chrome cases passed, including the A/B demo and the 390 px layout regression. |
| Live Chrome audit | Executed the actual learner journeys above on the normal runtime, separate from regression test servers. Baseline defects were reproduced. Final focused runs confirmed the fixes, including the post-grade count correction. |
| `scripts/validate_content.py --strict --stage S1/S4 --review-policy learner` | Both passed at existing thresholds. Both corresponding `--review-policy human` commands exited 1. |
| Independent SQL fixture execution | 18 fixture pairings, 12 query formulations, 36 successful restricted-worker comparisons against independently calculated rows. |
| `alembic -c backend/alembic.ini upgrade head`, `current`, `check` | Fresh migration passed. Head was `0007_ai_review`, with no pending operations. |
| `scripts/import_books.py lessons`, `scripts/reset_demo.py`, `scripts/seed_demo.py`, `scripts/verify_demo.py` | Six passages committed. Reset, seed and authored replay succeeded in the dedicated audit checkout. A stray temp demo path was rejected by the allowlist as intended. |
| `scripts/check_ollama.py` | Passed against the audit DB using the installed model. Chrome additionally exercised the real unavailable-provider fallback. |
| `scripts/evaluate_retrieval.py`, `scripts/simulate_policy.py` | Passed with draft-labeled retrieval queries and synthetic policy trajectories. |

**GitHub CI:** The exact starting revision passed both hosted jobs. The audited product revision also passed both hosted jobs. The hosted jobs run on Ubuntu and cover application tests, static checks, the S4 learner gate, fresh migration and the frontend build. Browser, Ollama and OS-worker conclusions in this report come from local Mac runs. [Baseline CI](https://github.com/Aadit5gupta/adaptive-dbms-tutor/actions/runs/45167234448) · [Audited product CI](https://github.com/Aadit5gupta/adaptive-dbms-tutor/actions/runs/45170749595)

## 8. Defect disposition

| Severity | Finding | Outcome |
|---|---|---|
| P2 | A chosen topic resumed a mixed session on another topic. | Fixed. The targeted session resumed only the selected scope in regression and Chrome. |
| P2 | A detector answered correctly earlier could later count as a new independent signal. | Fixed. Replay remains recorded as practice and no longer escalates the hypothesis. |
| P2 | Higher open-item hints repeated an incomplete model fragment. | Fixed. Three progressive curated prompts and evidence exclusion checked. |
| P2 | The model gave incorrect advice about unmatched rows in the count exercise. | Fixed for that reviewed exercise and mismatch path. The correct explanation and citation were observed in Chrome. |
| P2 | SQL preview errors lacked actionable distinctions. | Fixed. Syntax/schema and execution-limit messages checked in Chrome, with additional categories covered by regression. |
| P2 | At 390 px the signed-in lesson widened the entire page. | Fixed by containing horizontal scroll in the lesson. |
| P2 | Demo lesson presented literal Markdown and no readable example table. | Fixed. Shared renderer and visible semantic table checked. |
| P3 | Recent attempts within the same second can display in a different order from their submission. | Open. The order uses a same-second tie-break. Persisted results and recommendation did not change. |
| P3 | Single-signal text uses plural grammar. | Open. Signal counts and statuses are correct. |
| P3 | Chrome requests a missing favicon. | Open. Cosmetic 404. |

**Remaining verified defects:** 0 P0, 0 P1, 0 P2 and 3 P3. Scope gaps and external blockers are listed separately above.

## 9. Demonstration instructions

1. Use an Apple Silicon Mac. From the repository, apply the migrations, import the reviewed lessons, and start FastAPI and Vite as shown in the README. Keep the app on loopback. Open Ollama with `qwen3:1.7b` already installed.
2. Run `python scripts/reset_demo.py`, `python scripts/seed_demo.py` and `python scripts/verify_demo.py` against the marked demo database. Start the backend with `DBMS_DEMO_ENABLED=true`. Check readiness and run `python scripts/check_ollama.py` before presenting.
3. Open `http://127.0.0.1:5173/demo`. Use the two mapped wrong answers for each learner. Show the distinct recommendation, lesson and two fresh checkpoints. Ask why the unmatched branch remains and what its right-side columns contain.
4. Preview and submit the JOIN count exercise. Explain that hidden fixtures verify cases with duplicate names and zero matches. Open Library and show the reviewed original lesson in search and the **0 of 5 indexed** book count.
5. If inference is unavailable, demonstrate the labeled curated explanation. State the actual scope and approval status and describe the model as tutoring support. [Setup](../README.md) · [Exact learner walkthrough](demo.md)
