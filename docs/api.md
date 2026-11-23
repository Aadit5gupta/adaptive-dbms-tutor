# API contracts

All application endpoints use the `/api/v1` prefix. The API schema is available at `/openapi.json` on the local backend. Dates and times in persistence use UTC epoch seconds. Version references use the canonical `logical_id@version` format.

## Readiness

`GET /api/v1/health` returns HTTP 200 and `{"status":"ok","database":"ready"}` when the database is at the current revision. An unavailable or unmigrated database yields HTTP 503 with `{"detail":"Apply the database migrations and retry.","code":"db_not_ready"}`.

## Assessment persistence

An assessment item has a stable ID within a user's session and refers to a single immutable question version. Attempts store that item and version, the user's idempotency key, a request fingerprint, and the committed feedback. Session references come from the server. MCQ option ordinals are stored as `selected_option_index` and range from 0 to 3.

Published question options and SQL specifications must be inserted before their question version in the same transaction. Their deferred foreign keys validate at commit, and the version prevents subsequent inserts, edits, or deletion.
