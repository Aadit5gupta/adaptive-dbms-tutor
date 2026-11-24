# Learner A/B demonstration

The Chrome suites use temporary databases and curated tutoring. Run the synthetic suite and the original-content demo separately.

```sh
DBMS_TEST_CHROME=1 npm --prefix frontend run test:e2e
DBMS_TEST_AUTHORED=1 DBMS_TEST_CHROME=1 npm --prefix frontend run test:e2e -- authored-demo.spec.ts
```

The authored demo uses the explicit S1 learner gate. The separate-context review and SQL result checks are recorded in the [educational review](educational-review.md). Run the setup commands from the [README](../README.md), then reset and seed.

```sh
python scripts/validate_content.py --strict --stage S1 --review-policy learner
python scripts/reset_demo.py
python scripts/seed_demo.py
python scripts/verify_demo.py
```

Run the backend with `DBMS_DEMO_ENABLED=true` and open `http://127.0.0.1:5173/demo`. Between walkthroughs, choose **Reset demo**, then **Reset both learners**. This clears both synthetic learners' progress, open activities and tutor chats, and returns the page to Learner A.

## Five-to-ten-minute walkthrough

1. Select **Learner A**. In the diagnostic, choose the answer claiming that only one ticket may reference the account. Observe the possible hypothesis.
2. Start practice and choose the answer claiming the foreign-key value must occur only once in Members. Observe **KEYS-02** move to active.
3. Open the recommended lesson. Ask why two tickets may refer to a single account. Ask a follow-up about what a separate uniqueness restriction changes. Compare the source references in the response.
4. Open checkpoints. Choose **The badges with NULL and office 2 are accepted** for the issuing-office question and **UNIQUE on Bookings.room_id** for the room constraint question. Confirm resolution and a different recommendation. Reload to verify persisted progress.
5. Switch to **Learner B**. Choose INNER JOIN for the route report that needs all routes. In practice, choose the option that keeps one null-extended row for an unmatched customer after INNER JOIN. Observe the distinct **SQL-JOIN-01** hypothesis.
6. Open B’s lesson. In SQL practice, run and submit a query that returns every customer with a count of orders, including zero. The preview uses visible rows and submission grades against the published datasets.
7. Open Library and verify **4 of 5 indexed**. Search for `ON DELETE CASCADE` to show the exact Runestone source and its license. On the relational keys lesson page, ask the tutor what happens to jobs when their machine is deleted under `ON DELETE CASCADE`. Confirm the tutor cites the book passage. Compare a real Ollama reply with curated tutoring by restarting the backend with `TUTOR_PROVIDER=curated` if desired.

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
python scripts/check_ollama.py  # After importing the reviewed original lessons
```

Current observed gate results are recorded in the [test report](test-report.md).
