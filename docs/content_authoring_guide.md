# DBMS Mentor — human content authoring and review guide

**Authority:** `../MASTER_PLAN.md` v1.2 §§3, 6, 8. This guide supplies examples of the **canonical data contract** and reviewer checklist. The actual content schemas implemented in S0.2 must match these names and enums. Examples below are **drafts**, not approved educational material; never copy a placeholder reviewer name/date into verified content.

## A. Review and selection rules

| `review_status` | What it means | Available to learners? |
|---|---|---|
| `draft` | Generated, incomplete, or not yet manually verified | **No** |
| `author_verified` | Human owner manually checked answer, distractors, explanation, source, ambiguity and relevant SQL outputs | **Yes**, if rights/content dependencies are satisfied |
| `independent_verified` | Independent second human reviewed the material | **Yes** |

`enabled` is a **separate boolean** on misconception *definitions*, not a review status. Learner-specific misconception state is `possible|active|improving|resolved`, stored per learner. An AI may draft content and offer checks but may never set approval status or invent a human review. All approved content records require real `author`, `verified_by`, `verified_on`, `second_review`, `ai_assisted`, and documented source/provenance. When no second human reviewed it, `second_review: false` must be explicit.

## B. Question identity and pools

Every question or SQL task is a logical `id` with immutable positive integer `version`. Refer to the exact published version as `id@version`, for example `q_keys_fk_001@1`. Revisions make a new version; never mutate a published version. Two versions of one logical question **do not** count as two independent detector signals. Allowed `pool` values, exactly:

- `practice` — ordinary practice and mapped distractor detectors.
- `diagnostic` — screening/probes and optionally mapped detectors.
- `checkpoint` — reserved for remediation, unavailable in ordinary practice/diagnostic; each learner must not have seen it already.
- `pre_test_a`, `post_test_b` — held-out evaluation forms; never used in training mastery or practice.

**`detector` is NOT a pool.** A wrong MCQ option mapped to a misconception makes that question a detector for that code. Detector questions normally belong to `practice` or `diagnostic`. A four-option MCQ has exactly one correct option; a wrong option may map to **at most one** specific misconception and only if the mapping is educationally defensible. A learner seeing the answer-revealing hint removes that attempt's independence for misconception evidence.

## C. Draft MCQ — example only

```yaml
id: q_keys_fk_001
version: 1
type: mcq
pool: practice
subtopic_id: relational.keys
difficulty: easy
review_status: draft
stem: >
  Orders.customer_id references Customers.id. Which statement is correct?
options:
  - text: A customer may appear in multiple Orders rows.
    correct: true
  - text: Every customer may appear in at most one Orders row.
    correct: false
    misconception_code: KEYS-02
  - text: The referencing column must also be Orders' primary key.
    correct: false
  - text: Every foreign key forbids NULL even without a NOT NULL constraint.
    correct: false
explanation: >
  A foreign key enforces reference integrity, not uniqueness on the
  referencing side; many orders may reference the same customer.
source:
  kind: authored
  factual_reference_url: https://opentextbc.ca/dbdesign01/
  reproduced_book_text: false
author: null
verified_by: null
verified_on: null
second_review: false
ai_assisted: true
```

All reviewer fields above are deliberately unfilled; this item must remain a **draft**. `factual_reference_url` is not a book-local indexing approval. If actual excerpts are copied or closely adapted, link a hash-matched, approved `source_section_clearance_id` and obey its license instead.

## D. Draft misconception definition — example only

```yaml
code: KEYS-02
subtopic_id: relational.keys
name: Assumes foreign keys are unique on the referencing side
explanation: >
  Conflates the constraint on referenced candidate keys with uniqueness
  of the foreign-key values in the referencing table.
review_status: draft
enabled: false
evidence_rule:
  min_distinct_logical_questions: 2
  ignore_after_revealing_hint: true
detector_question_refs:
  - q_keys_fk_001@1
  - q_keys_fk_002@1
remediation_lesson_ref: lesson_fk_multiplicity@1
checkpoint_question_refs:
  - q_keys_fk_cp1@1
  - q_keys_fk_cp2@1
retrieval_query: foreign key many to one referencing side uniqueness
source:
  kind: authored
  factual_reference_url: https://opentextbc.ca/dbdesign01/
```

To set `enabled: true`, this definition must be human-approved AND every referenced question/lesson must exist as a reviewed immutable version. Both detector logical IDs must be different and have a wrong option mapped specifically to `KEYS-02`; both checkpoint logical IDs must differ from one another and from detector IDs. Checkpoints must have `pool: checkpoint`, with no prior exposure to the learner in remediation. An enabled definition missing any requirement fails `validate_content.py --strict`.

**Initial two patterns:** `KEYS-02` (foreign keys incorrectly assumed unique), `SQL-JOIN-01` (INNER vs LEFT JOIN when there are unmatched rows). Each requires ≥2 independent detectors, ≥2 distinct reserved checkpoints, and ≥1 authored/cleared remediation lesson. That is at least 8 reviewed detector/checkpoint MCQs total for two patterns; S1 further needs ≥4 ordinary practice MCQs (≥12 reviewed MCQs total).

## E. Draft SQL exercise — example only

```yaml
id: sql_join_001
version: 1
type: sql
pool: practice
subtopic_id: sql.joins
difficulty: easy
review_status: draft
dialect: sqlite
min_sqlite_version: "3.35"
prompt: List every customer with their number of orders, including customers with zero orders.
visible_fixture: content/sql_fixtures/shop_visible.sql
hidden_fixtures:
  - content/sql_fixtures/shop_hidden_a.sql
  - content/sql_fixtures/shop_hidden_b.sql
reference_query: |
  SELECT c.id, c.name, COUNT(o.id) AS order_count
  FROM customers AS c
  LEFT JOIN orders AS o ON o.customer_id = c.id
  GROUP BY c.id, c.name;
compare:
  order_sensitive: false
  duplicate_sensitive: true
  column_names_matter: false
expected_results:
  - fixture: content/sql_fixtures/shop_visible.sql
    expected_result_file: tests/fixtures/expected/shop_visible.json
  - fixture: content/sql_fixtures/shop_hidden_a.sql
    expected_result_file: tests/fixtures/expected/shop_hidden_a.json
  - fixture: content/sql_fixtures/shop_hidden_b.sql
    expected_result_file: tests/fixtures/expected/shop_hidden_b.json
source:
  kind: authored
  factual_reference_url: https://runestone.academy/ns/books/published/practical_db/index.html
author: null
verified_by: null
verified_on: null
second_review: false
ai_assisted: true
```

**These fixture paths are proposed outputs for Codex to create, not files that already exist.** Hidden fixtures must not be accessible from learner API responses or the frontend bundle. Correctness is not just “reference SQL executed without error”: a human must independently specify expected rows/duplicate counts (or a separately reviewed reference implementation), and test correct alternative SQL formulations on all fixtures. Include unmatched rows, duplicate rows, zero matches, `NULL`, and counting pitfalls. During validation, run the reference query against each fixture and compare it with the independently verified expected result. `Run` uses visible data only, while `Submit` grades on hidden data. No hint about JOIN type should automatically become a confirmed misconception.

## F. Lessons

A lesson version has `id`, `version`, `subtopic_id`, `review_status`, `title`, `source`, `author`, `verified_by`, `verified_on`, `second_review`, `ai_assisted` and Markdown body. The body contains: clear explanation, one small example with tables/rows, one **contrast** addressing the misconception, and a link or action for approved checkpoint practice. Reproduced or closely adapted passages require matching section rights clearance; independently authored educational explanations still cite fact-check sources without pretending a locally indexed passage exists.

## G. Validation modes and realistic budget

- `python scripts/validate_content.py --strict`: complete referential/schema integrity for all content; all enabled definitions have full detector/lesson/checkpoint coverage; **zero enabled definitions is permitted at S0**.
- `python scripts/validate_content.py --strict --stage S1`: additionally demands ≥2 fully covered enabled definitions, ≥12 reviewed MCQs (≥4 ordinary), ≥2 reviewed lessons, ≥1 SQL task validated on all fixtures. Failure is a true build gate for declaring S1 complete.
- `python scripts/validate_content.py --strict --stage S4`: demands the lean-MVP thresholds in the master plan; stage-specific gate should not silently downgrade targets.
- The S1 minimum is **not** enough for the seven-domain diagnostic: show uncovered domains as unassessed. Content for the S4 product should be prioritized by user utility and correctness rather than artificial counts.

A reasonable **planning** pace is around 5–8 manually verified questions per week for one reviewer, but record real throughput rather than claiming that pace as a fact. Codex can draft batches, derive edge cases and format files to accelerate reviews, never approve itself.

## H. Human sign-off checklist (per item)

- [ ] I independently solved the MCQ or verified SQL expected results, without relying on the generated key alone.
- [ ] Exactly one MCQ option is correct, and distractors are unambiguously wrong for valid reasons.
- [ ] Misconception mappings are specific and justified; incorrect query output alone is not diagnostic proof.
- [ ] The source URL/rights clearance and required attribution are accurate; no unreviewed book excerpts or third-party figures are embedded.
- [ ] Question/lesson is not a disguised duplicate of its detector, checkpoint or held-out counterpart; references use `@version`.
- [ ] Human identity and true review date are recorded, `second_review` indicates reality, and `ai_assisted` is truthful.
- [ ] The stage-specific validator, SQL test suite and exposed-answer tests pass.

Only after this checklist may the **human** mark the item `author_verified` or (with a real second person) `independent_verified`.
