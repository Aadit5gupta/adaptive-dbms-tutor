# API contracts

All application endpoints use the `/api/v1` prefix. The API schema is available at `/openapi.json` on the local backend. Dates and times in persistence use UTC epoch seconds. Version references use the canonical `logical_id@version` format.

## Readiness

`GET /api/v1/health` returns HTTP 200 and `{"status":"ok","database":"ready"}` when the database is at the current revision. An unavailable or unmigrated database yields HTTP 503 with `{"detail":"Apply the database migrations and retry.","code":"db_not_ready"}`.

## Assessment persistence

An assessment item has a stable ID within a user's session and refers to a single immutable question version. Attempts store that item and version, the user's idempotency key, a request fingerprint, and the committed feedback. Session references come from the server. MCQ option ordinals are stored as `selected_option_index` and range from 0 to 3.

Published question options and SQL specifications must be inserted before their question version in the same transaction. Their deferred foreign keys validate at commit, and the version prevents subsequent inserts, edits, or deletion.

## Local demo

With `DBMS_DEMO_ENABLED=true`, the application recognizes only the fixed demo identities `a` and `b` and connects to the marked demo database.

- `GET /demo/{learner}` returns progress, recommendation and any open activity.
- `POST /demo/{learner}/sessions` accepts `{"activity":"diagnostic"}`. Activity values also include `practice`, `checkpoint` and `sql`.
- `POST /demo/{learner}/sessions/{session_id}/answer` accepts `{"item_id":"...","option_index":1}` and an `Idempotency-Key` header.
- `GET /demo/{learner}/lesson` returns the current recommended lesson with its source URL.
- `POST /demo/{learner}/sessions/{session_id}/sql/run` and `/sql/submit` accept `{"item_id":"...","query":"SELECT ..."}`. Submit requires an `Idempotency-Key` and commits feedback and learner progress.

Mutations require an allowed loopback origin. Hidden fixtures and reference queries are excluded from the API.

## Source catalog and search

`GET /library/books` returns the five source records, current clearances and counts derived from documents present in the full-text index. `GET /library/search?q=foreign%20key&topic=relational.keys` ranks up to six passages using SQLite BM25. Topic-scoped results come first. Results include the stored attribution, source URL, optional license URL and a bounded excerpt.

## Curated tutor

The local demo exposes `POST /tutor/ask`, `/tutor/explain` and `/tutor/hint`. Send a short `query`, an optional curriculum `topic_id`, `mode`, and `hint_level` from 1 to 3. Replies include status and citations selected from retrieved or same-topic reviewed material. If no approved evidence is available, the tutor reports that state.

## Accounts and privacy

Register and sign in at `POST /auth/register` and `POST /auth/login` with `email` and `password`. Successful responses set an opaque HttpOnly, SameSite=Lax session cookie. The session expires after one day and `POST /auth/logout` revokes it. Cookie security is configurable for HTTPS.

`GET /me` returns the signed-in account. `PATCH /me` updates the learning goal, experience level and daily minutes. `GET /me/export` downloads the account's learning data. `DELETE /me` deletes the account and its related records. Mutation requests need an exact allowlisted Origin or same-origin Referer.

## Signed-in learning

The curriculum, versioned lessons, assessments, practice, revision, SQL Lab and progress endpoints require a signed-in session. `POST /practice/sessions` accepts a topic, optional difficulty and a mode of `practice` or `review`. `POST /assessments/start` starts a screening when the topic is omitted or a targeted probe when supplied.

Session responses carry a current item, total and remaining counts. Send a choice with an idempotency key to `/practice/sessions/{id}/answer` or `/assessments/{id}/submit`. `POST /practice/checkpoints` uses the current learner's recommended and still-eligible remediation. Progress, hypotheses and recommendations can be fetched from `/progress`, `/misconceptions` and `/recommendations/next`.

A targeted session only resumes a session whose items are all in the requested topic. For a reviewed SQL exercise, start a session with `POST /sql/exercises/{id}/sessions`. Run or submit a query to the matching endpoint with the returned session and item IDs. Session ownership, immutable versions and secret-free feedback apply to both routes.

## Tutor follow-ups

Signed-in tutor requests can include the `conversation_id` from the first reply. The application uses the latest three turns with the saved topic and approved sources. `GET /tutor/conversations/{id}` returns the most recent messages to the owning account. The loopback demo uses `/demo/tutor/{learner}/...` and stores its history in the dedicated demo database.

A practice hint uses its `item_id` and advances through three curated reasoning prompts. Levels 2 and 3 still make the response ineligible as independent evidence. Diagnostics and checkpoints accept no item-specific tutor hints. SQL mistake explanations use a completed `attempt_id`, the assessed topic, the visible exercise goal and a safe feedback category. The original LEFT JOIN count exercise uses a reviewed explanation on result mismatch. Preview errors expose safe categories for syntax/schema, unsupported statements, execution limits and result limits.
