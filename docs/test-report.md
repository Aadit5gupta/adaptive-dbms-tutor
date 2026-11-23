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

S1 introduces the learner A/B demo. S5 requires a separately invoked real Ollama integration check.
