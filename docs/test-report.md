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
