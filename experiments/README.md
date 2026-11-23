# Reproducible engineering evaluation

Run these commands from the repository root in the backend environment.

```sh
python scripts/simulate_policy.py
python scripts/evaluate_retrieval.py --k 4
python scripts/check_ollama.py --provider-only
python scripts/check_ollama.py
```

The policy simulation reports synthetic score paths, confidence and recommendations. It covers repeated questions, independent answers and a two-signal misconception. These are controlled engineering scenarios.

The retrieval script computes hit@k and mean reciprocal rank against passages that are actually searchable. Its query labels are currently drafts. The script exits with the missing lesson versions when the expected corpus has not been approved and indexed. The backend tests separately verify the metric calculation on a temporary synthetic corpus.

The Ollama provider check uses a test-only LEFT JOIN passage. The second Ollama command uses the reviewed application corpus. See the [test report](../docs/test-report.md) for observed results.

A human pilot would require faculty approval, consent and held-out assessment forms. No participants have been recruited and this project reports no learning-gain measurements.
