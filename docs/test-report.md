# Test report

## 23 November 2026

| Check | Observed result |
|---|---|
| macOS environment | 27.2.1 (26B131) arm64, Python 3.12.16, SQLite 3.54.1, Node 26.13.1, npm 11.20.0 |
| Backend tests | 27 passed, covering content validation, source clearance, and database readiness |
| Ruff and mypy | Passed |
| Strict content validator | Passed with five catalog entries and zero approved sections or learning items |
| S1 stage gate | Exited 1 because human-reviewed content minima are unmet |
| Fresh migration | Upgrade and current passed at `0001_baseline` |
| Frontend | Lint, typecheck, build and two Vitest tests passed |
| Live loopback smoke | Vite served `/learn` and proxied `/api/v1/health` successfully |

At S0 exit the full local suite passed again. Strict validation checked the draft JOIN reference against three fixtures. GitHub rejected workflow creation because the active CLI token lacks `workflow` scope.

S1 introduces the learner A/B demo. S5 requires a separately invoked real Ollama integration check.

## S1 engineering boundary

- Backend suite passed 84 tests on macOS arm64. Ruff, strict mypy, structural content validation and Alembic migration checks passed.
- Frontend lint, typecheck, build and two Vitest tests passed. Headless Chrome Playwright passed two tests with synthetic fixture content, including the A/B learner flow, refresh, checkpoint resolution, real SQL preview/submission and cross-origin mutation rejection.
- Reset and seed ran against the dedicated local demo database. The real-content replay and S1 stage gate exited 1 because the authored materials await human review. The synthetic replay passed in the backend test suite.
- GitHub Actions remains pending the CLI workflow scope. Apple Silicon macOS is the tested SQL worker platform.

## S2 engineering boundary

89 backend tests, two Vitest tests and two Chrome Playwright tests passed. Backend and frontend lint, type checks, build and strict content validation passed. The test-only A/B replay passed again. The actual demo verification exited 1 at the unchanged human review gate.

## S3 engineering boundary

95 backend tests, two Vitest tests and three Chrome Playwright tests passed. Lint, types, build, fresh Alembic upgrade and strict validation passed. Synthetic tests confirmed exact-hash approved import, BM25, revocation filtering, application-owned citations, provider fallback and curated tutoring in Chrome. The actual catalog shows zero of five books indexed and no approved lessons are available yet.

## S4 engineering boundary

102 backend tests, two Vitest tests and four Chrome Playwright tests passed. Backend and frontend lint, type checks, frontend build and the Alembic schema check passed. Six authored SQL reference queries passed the restricted worker across all three fixtures. The S4 validator exited 1 because the 30 MCQs, six lessons, six SQL exercises and three misconception patterns remain drafts awaiting review.

## S5 engineering boundary

116 backend tests, two Vitest tests and four Chrome Playwright tests passed on the 8 GiB Mac. Ruff, mypy, frontend lint, typecheck, build, structural content validation and Alembic schema checks passed.

The opt-in real `qwen3:1.7b` check correctly explained why a LEFT JOIN preserves unmatched rows and why their right-side columns are NULL. The follow-up used the same test evidence. The approved-corpus check exited 1 because no reviewed passages are indexed.

The synthetic policy script produced score paths of 0.60 → 0.68 → 0.744 for three correct answers. The independent sequence reached emerging confidence, while the repeated sequence remained insufficient. Two independent mistakes recommended remediation. The retrieval metric tests passed on a temporary corpus. The release-corpus evaluator reported all six expected lesson versions missing pending review.

## S6 fresh-clone and live verification

Cloned private GitHub revision `5df42ea` into a new temporary directory on 23 November 2026. Installed both locked dependency sets and applied a fresh Alembic upgrade through `0006_tutor_threads`. The Alembic schema check, strict content validator, 117 pytest tests, Ruff, strict mypy, frontend lint, typecheck, build, two Vitest tests and four headless Chrome Playwright tests passed. The checkout stayed clean after testing.

The clone's reset and seed commands ran against its dedicated demo database. The authored demo replay, S4 content gate and approved-corpus Ollama check exited 1 at the pending-review gates. The separate real-model explanation and follow-up passed again on the same Mac.

The workspace frontend and backend were started on loopback. The frontend, proxied health request, library catalog and both demo identities responded successfully. Hosted Actions passed for the clean-clone revision. [GitHub Actions run](https://github.com/Aadit5gupta/adaptive-dbms-tutor/actions/runs/45136868018)

## Post-build educational verification · 23 November 2026

| Check | Observed result |
|---|---|
| Review of original bank | Separate-context AI review confirmed 30 MCQ keys, six lessons and three distinct misconception patterns. All 45 existing items, including the six SQL exercises, passed after targeted revisions. |
| Independent SQL execution | SQLite 3.54.1 on Apple Silicon macOS. Independently derived rows matched all 18 stored results. Reference and alternate queries passed all 36 restricted-worker runs. Nine incorrect variants disagreed with an expected result at least once. |
| Backend regression | `bash scripts/check_backend.sh backend/.venv/bin` passed 130 pytest cases, Ruff, strict mypy and structural content validation. This covered a migration with existing immutable human-reviewed content, linked options and an FTS passage. Alembic detected no schema drift at `0007_ai_review`. |
| Content gates | S1 and S4 passed with `--review-policy learner`. Both human-only gates exited 1 with zero items in the human cohort. The learner bank has 30 MCQs including 17 ordinary practice questions, six lessons, six checked SQL tasks and three fully covered patterns. |
| Frontend regression | ESLint, TypeScript, production build and two Vitest tests passed. Four synthetic Chrome cases passed. The separate authored Chrome case passed for both learners, including evidence, remediation, checkpoints, persisted progress, attributed curated follow-up, SQL preview and submission. |
| Authored CLI replay | `scripts/seed_demo.py` and `scripts/verify_demo.py` passed. The replay verified the two learner hypotheses, checkpoint resolution and SQL grading on a disposable copy. |
| Real Ollama against the indexed corpus | `scripts/check_ollama.py` returned a correct LEFT JOIN explanation from `qwen3:1.7b`, with the original lesson and its Runestone chapter citation. The live demo API also produced two cited Ollama answers, explained NULL extension in the follow-up, and persisted all four turns. |
| Local source inventory | The lessons import indexed six original passages. The live Library showed zero of five books indexed. Strict validation found zero approved publisher sections. |
| Hosted regression | GitHub Actions passed on `2905a27`, including the S4 learner gate and a fresh Alembic migration. The SQL worker and real-model checks ran on the Mac. [GitHub Actions](https://github.com/Aadit5gupta/adaptive-dbms-tutor/actions/runs/45167065757) |
| Retrieval smoke | All six expected lessons ranked first in the six draft-labeled queries. Hit@4 and MRR were both 1.0 on this small smoke set. |

The earlier sections record the engineering baseline before publication. Human-only content coverage and publisher section clearance remain open. [Educational evidence](educational-review.md) · [Rights review](section-rights-review.md)

## Final product acceptance

The final audit reran the existing tests and used installed Chrome against the normal local runtime. Product revision `3b56e5c` passed 138 backend tests, two Vitest tests, six Chrome regression cases, both learner gates and real Ollama. The [acceptance report](FINAL_ACCEPTANCE_REPORT.md) records the browser evidence, fixes, human-only gate failures and separate local, public and human-study decisions.

## Browser demo reset

139 backend tests, two Vitest tests and six Chrome cases passed. Browser coverage exercised cancellation, reset with an open activity, both fresh learner states and a new diagnostic after reload. The API test checks loopback and Origin requirements, replay rejection and an in-flight tutor reply. Ruff, mypy, frontend lint/typecheck/build, S4 learner validation and the authored CLI replay passed. The live Chrome confirmation opened and canceled at 390 px.

## Learn coverage, 25 November 2026

| Check | Actual result |
|---|---|
| `bash scripts/check_backend.sh backend/.venv/bin` | 139 pytest tests passed, including the restricted SQL worker regressions. Ruff, mypy and strict validation passed. |
| `python scripts/validate_content.py --strict --stage S1 --review-policy learner` and the S4 equivalent | Both passed with 46 MCQs, 33 ordinary practice questions, 22 lessons, six checked SQL exercises and three enabled patterns. Both default human-only gates exited 1 with zero qualifying items. |
| Frontend lint, typecheck, Vitest and production build | All passed, including both Vitest tests. |
| Chrome Playwright, standard and `DBMS_TEST_AUTHORED=1` suites | Four standard and three authored tests passed. The new test opened every Learn domain, found all 24 topics and zero pending labels, opened the new weak-entity lesson, and completed its practice question. |
| `python scripts/verify_demo.py` | Both learners passed the original detector, remediation and checkpoint replay. Learner B's SQL answer passed the grading fixtures. |
| `python scripts/import_books.py lessons` and `python scripts/import_books.py --demo lessons` | Both local databases published the new content. A catalog and scoped BM25 probe checked all 16 new lessons in each database. Each database has 22 original lesson passages and zero book passages. |
| SQLite worked examples | The correlated EXISTS query returned the qualifying workshop once with three matching bookings. The indexed lookup produced the documented SEARCH plan. The decomposition projections rejoined to the example tuples. |
| `python scripts/check_ollama.py` and targeted weak-entity probes | Real `qwen3:1.7b` cited the original LEFT JOIN lesson in the standard check and the new weak-entity lesson in both targeted probes. The first weak-entity reply misstated where duplicate locker numbers can occur, despite naming the correct composite key. The concrete two-wing prompt correctly explained that each wing can have a locker 7 and identified both by the wing code and locker number. |

## Licensed book retrieval, 25 November 2026

| Check | Actual result |
|---|---|
| Backend and frontend | 145 pytest tests, two Vitest tests, Ruff, mypy, frontend lint, typecheck and build passed. New regressions verify exact publisher scope, license, verifier, hash, idempotent FTS import and genuine source metadata. |
| Learner content and demo | Strict validation and S1/S4 learner gates passed with two indexable publisher records. The authored CLI replay passed. Four standard and three authored Chrome tests passed. Chrome showed 2 of 5 indexed in the authored Library and verified the Runestone search result, exact section link and license link. |
| Local import and search | Application and dedicated demo imports each reported 24 searchable passages. The live Library returned one passage each from Runestone and BCcampus. Searching for orphan records returned the BCcampus reference first. |
| Real Ollama | `python scripts/check_ollama.py --book` correctly explained that deleting the parent machine under ON DELETE CASCADE deletes both referencing jobs and cited the Runestone book excerpt. The original-lesson LEFT JOIN check also passed. |

## Shea and DataField book retrieval, 25 November 2026

The two snippets were matched to the publisher HTML and checked against the published license notices. Strict validation and both S1/S4 learner gates passed with four indexable publisher scopes. Pytest 145, Vitest 2, Ruff, mypy, frontend lint, typecheck and build passed. All seven Chrome scenarios passed across the standard and authored suites. The authored Library showed 4 of 5 indexed and returned the Shea license and exact DataField section link.

Both local imports reported 26 searchable passages and the authored Learner A/B CLI replay passed. The live Library returned one indexed section for each of the four books. Real Ollama cited the Shea excerpt when explaining SQLite index storage and the DataField excerpt when explaining transaction atomicity. OpenStax retained zero indexed sections.

## Library and Tutor navigation, 25 November 2026

Pytest 146, Vitest 2, Ruff, mypy, frontend lint, typecheck and production build passed. Strict validation and the S4 learner gate passed. The new backend regression verified that the filter finds the requested source kind, that the FTS excerpt includes a match late in a long passage, and that the full tutor passage stays available.

Four standard and four authored Chrome scenarios passed. At 390 px, the new scenario filtered for textbooks, reloaded the same query, opened a topic-specific tutor with an editable draft, received a curated textbook citation and returned to the same search via Back. It then filtered for lessons and opened the signed-in lesson and its tutor. The real Ollama textbook citation and authored Learner A/B CLI replay also passed.

## One-click practice hints, 25 November 2026

Pytest 146, Vitest 2, Ruff, mypy, frontend lint, typecheck, production build, strict content validation and the S4 learner gate passed. The authenticated tutor test verified questionless hints, a clue for repeated foreign-key values, a generic response to a request for the correct option, no model calls for item hints, account isolation and ordered hint levels. It also confirmed that an advanced hint preserves the existing independent-evidence restriction.

Four standard and five authored Chrome scenarios passed. At 390 px, a prepared hint worked with one click, the outgoing request had no question text, the optional typed clue responded to the foreign-key question, all three prepared levels could be opened in order, and the next practice item started with a fresh hint control.

The authored Learner A/B CLI replay and real Ollama textbook citation also passed.
