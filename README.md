# Adaptive DBMS Tutor

Adaptive DBMS Tutor is a local-first DBMS and SQL learning platform. Deterministic grading drives mastery, misconception evidence and recommendations. The tutor uses SQLite FTS5, BM25 and the local Ollama model to explain reviewed material.

The app runs on Apple Silicon macOS. The AI-verified learner bank includes 46 MCQs, 22 original lessons, six SQL exercises and three enabled misconception definitions. All 24 Learn topics have learner material. The tutor can retrieve the 22 original lessons. The Library shows five catalog entries and zero indexed books. [Educational review](docs/educational-review.md) · [Section rights review](docs/section-rights-review.md)

- [Implementation status](IMPLEMENTATION_STATUS.md)
- [Architecture and schema](docs/architecture.md)
- [API contracts](docs/api.md)
- [Learner demo and review steps](docs/demo.md)
- [Test results](docs/test-report.md)
- [Evaluation commands](experiments/README.md)
- [Viva notes](docs/viva.md)
- [Master plan](MASTER_PLAN.md) and [decision log](DECISIONS.md)

## Ollama setup on macOS

Install the app from the [Ollama macOS instructions](https://docs.ollama.com/macos). Open Ollama and enable its CLI when prompted. Pull the model manually:

```sh
ollama pull qwen3:1.7b
ollama list
```

For a standalone CLI installation, run `ollama serve` in a separate terminal before pulling. The application and automated tests leave downloads to you. See the [model listing](https://ollama.com/library/qwen3:1.7b).

The default provider uses the loopback endpoint in [.env.example](.env.example). Curated tutoring takes over if Ollama is unavailable, busy, or `TUTOR_PROVIDER=curated` is set. Automated tests use a mock. To verify the installed model with a small test passage, run:

```sh
python scripts/check_ollama.py --provider-only
```

Once the reviewed lesson index is populated, run `python scripts/check_ollama.py` for the reviewed-corpus check. The provider uses a 4,096-token context, up to 384 output tokens, one inference slot and a 30-second deadline.

## Local backend

Install Python 3.11 or newer and [uv](https://docs.astral.sh/uv/). From this directory:

```sh
uv sync --project backend --python 3.12 --locked --extra dev
source backend/.venv/bin/activate
cp -n .env.example .env
python -m alembic -c backend/alembic.ini upgrade head
python scripts/import_books.py lessons
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
```

Check readiness at `http://127.0.0.1:8000/api/v1/health` and view the API contract at `http://127.0.0.1:8000/docs`. Paths in `.env` are relative to the repository root. The app and demo databases must use distinct paths.

```sh
bash scripts/check_backend.sh
```

## Local frontend

Install Node.js 22.12 or newer. With the backend running, open a second terminal in this directory:

```sh
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the local backend on port 8000.

```sh
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
```

The [test report](docs/test-report.md) records verified results.

## Learner A/B demo

Use the backend virtual environment from the previous setup. The scripts operate on the marked `data/demo.sqlite` database. Reset removes the two synthetic learner records and their progress.

```sh
python scripts/reset_demo.py
python scripts/seed_demo.py
python scripts/verify_demo.py
DBMS_DEMO_ENABLED=true python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
```

Run Vite in the second terminal and open `http://127.0.0.1:5173/demo`. To repeat the demo, choose **Reset demo**, then **Reset both learners**. The replay uses the learner content gate. The default human-only content gate remains available for reporting human review coverage. See the [authoring and sign-off guide](docs/content_authoring_guide.md).

The automated browser tests use isolated databases. Run the synthetic suite or the original learner bank in the existing Google Chrome installation.

```sh
DBMS_TEST_CHROME=1 npm --prefix frontend run test:e2e
DBMS_TEST_AUTHORED=1 DBMS_TEST_CHROME=1 npm --prefix frontend run test:e2e -- authored-demo.spec.ts
```

SQL execution support and limits are documented in the [SQL worker notes](docs/sql-worker.md).

## Signed-in learning

After migration, publish the reviewed local curriculum and build the lesson index with `python scripts/import_books.py lessons`. Open the frontend and create a local account. Use Settings to save a learning goal and experience level, export your learning data or delete your account.

The dashboard shows reviewed activity, coverage and the deterministic next recommendation. Practice and diagnostics resume on refresh. SQL Lab shows visible fixture rows and includes a SQLite-aware editor. Preview leaves your progress unchanged, and Submit grades against the published exercise's fixtures.
