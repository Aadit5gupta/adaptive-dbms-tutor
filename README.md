# Adaptive DBMS Tutor

Adaptive DBMS Tutor is a local-first DBMS and SQL learning project. Its deterministic assessment engine will track mastery and misconception evidence. A local tutor will use SQLite FTS5 with BM25 ranking to retrieve human-reviewed lessons and individually cleared book sections.

See the [master plan](MASTER_PLAN.md), [implementation status](IMPLEMENTATION_STATUS.md), and [decision log](DECISIONS.md) for current setup and verified milestones.

## Ollama setup on macOS

Install the app from the [Ollama macOS instructions](https://docs.ollama.com/macos). Open Ollama and enable its CLI when prompted. Pull the model manually:

```sh
ollama pull qwen3:1.7b
ollama list
```

For a standalone CLI installation, run `ollama serve` in a separate terminal before pulling. The application and automated tests leave downloads to you. See the [model listing](https://ollama.com/library/qwen3:1.7b).

Ollama integration is scheduled for S5. When available, the default provider will connect to the loopback endpoint in [.env.example](.env.example). Curated explanations will be available if Ollama is unavailable or `TUTOR_PROVIDER=curated` is configured. Model-free automated tests will use a mock, and real-model verification will be a separate command.
