# Learner A/B demonstration

The automated demo uses temporary synthetic test content and real Chrome browser interactions. It is independent of Ollama and can be run before the authored content is reviewed.

```sh
DBMS_TEST_CHROME=1 npm --prefix frontend run test:e2e
```

The authored-content browser demo requires the S1 gate to pass. The draft bank and independent SQL result checks are available in the [authoring guide](content_authoring_guide.md). Run the setup commands from the [README](../README.md), then reset and seed.

```sh
python scripts/validate_content.py --strict --stage S1
python scripts/reset_demo.py
python scripts/seed_demo.py
python scripts/verify_demo.py
```

Run the backend with `DBMS_DEMO_ENABLED=true` and open `http://127.0.0.1:5173/demo`.

## Five-to-ten-minute walkthrough

1. Select **Learner A**. In the diagnostic, choose the answer claiming that only one ticket may reference the account. Observe the possible hypothesis.
2. Start practice and choose the answer claiming the foreign-key value must occur only once in Members. Observe **KEYS-02** move to active.
3. Open the recommended lesson. Ask why two tickets may refer to a single account. Ask a follow-up about what a separate uniqueness restriction changes. Compare the source references in the response.
4. Open checkpoints. Choose **2 and 2** for the issuing-office question and **UNIQUE on Bookings.room_id** for the room constraint question. Confirm resolution and a different recommendation. Reload to verify persisted progress.
5. Switch to **Learner B**. Choose INNER JOIN for the route report that needs all routes. In practice, choose the option that keeps one null-extended row for an unmatched customer after INNER JOIN. Observe the distinct **SQL-JOIN-01** hypothesis.
6. Open B’s lesson. In SQL practice, run and submit a query that returns every customer with a count of orders, including zero. The preview uses visible rows and submission grades against the published datasets.
7. Open Library and report the displayed indexed book count. Compare a real Ollama reply with curated tutoring by restarting the backend with `TUTOR_PROVIDER=curated` if desired.

An eligible SQL solution for the reviewer:

```sql
SELECT c.id, c.name, COUNT(o.id)
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.id
GROUP BY c.id, c.name;
```

The real-model transport check is independent of the review gate:

```sh
python scripts/check_ollama.py --provider-only
```

Current observed gate results are recorded in the [test report](test-report.md).
