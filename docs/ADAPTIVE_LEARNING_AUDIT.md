# Adaptive learning audit

**Baseline** `0fa565b5193bd7e967365310d89725ce118dddc4` · **25 November 2026**

## Question inventory and publication

Read-only checks compared both application and demo databases with the current source bank. All 24 topic labels, all prerequisite edges, all 52 version hashes, every MCQ option and answer mapping, and all six SQL snapshots matched. The bank has **46 MCQs**, including 33 ordinary practice questions, three practice detectors, four diagnostic questions and six reserved checkpoints. There are zero evaluation MCQs and zero hard MCQs. All versions are `@1` and `ai_verified`.

A diagnostic item can be resumed while open, including through a narrower view of its original session. A graded diagnostic is excluded from new diagnostics. Practice takes unseen items first. A learner can deliberately repeat a practice item, with no new independent evidence. Checkpoints require eligible remediation and prior non-exposure. The linked misconception column identifies detector or checkpoint roles. Every row below is published in both databases and selectable through its activity under those conditions.

### Entities and attributes · `er.entities`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_er_entities@1` | Practice or revision | easy | — |

### Relationships and cardinality · `er.cardinality`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_er_cardinality@1` | Practice or revision | easy | — |

### Weak entities · `er.weak_entities`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_er_weak_entities@1` | Practice or revision | easy | — |

### Relations and constraints · `relational.relations`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_relational_relations@1` | Practice or revision | easy | — |

### Candidate, primary and foreign keys · `relational.keys`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_keys_checkpoint_badges@1` | Remediation checkpoints only | easy | KEYS-02 checkpoint |
| `q_keys_checkpoint_rooms@1` | Remediation checkpoints only | easy | KEYS-02 checkpoint |
| `q_keys_detector_tickets@1` | Diagnostic only | easy | KEYS-02 detector |
| `q_keys_detector_members@1` | Practice or revision | easy | KEYS-02 detector |
| `q_lean_keys_candidate_count@1` | Practice or revision | easy | — |
| `q_lean_keys_composite@1` | Practice or revision | easy | — |
| `q_lean_keys_fk_target@1` | Practice or revision | easy | — |
| `q_practice_keys_missing@1` | Practice or revision | easy | — |
| `q_lean_keys_superkey@1` | Practice or revision | medium | — |

### Relational operators · `relational.algebra`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_relational_algebra@1` | Practice or revision | easy | — |

### SELECT and WHERE · `sql.select`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_lean_select_between@1` | Practice or revision | easy | — |
| `q_lean_select_distinct@1` | Practice or revision | easy | — |
| `q_practice_select_columns@1` | Practice or revision | easy | — |
| `q_practice_select_where@1` | Practice or revision | easy | — |

### ORDER BY · `sql.ordering`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_lean_select_order@1` | Practice or revision | easy | — |

### INNER and LEFT JOIN · `sql.joins`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_join_checkpoint_households@1` | Remediation checkpoints only | easy | SQL-JOIN-01 checkpoint |
| `q_join_checkpoint_teams@1` | Remediation checkpoints only | easy | SQL-JOIN-01 checkpoint |
| `q_join_detector_routes@1` | Diagnostic only | easy | SQL-JOIN-01 detector |
| `q_join_detector_orders@1` | Practice or revision | easy | SQL-JOIN-01 detector |
| `q_lean_join_multiple@1` | Practice or revision | easy | — |
| `q_lean_join_count@1` | Practice or revision | medium | — |

### Aggregates, GROUP BY and HAVING · `sql.aggregation`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_lean_group_count@1` | Practice or revision | easy | — |
| `q_lean_group_filter@1` | Practice or revision | easy | — |
| `q_practice_count_null@1` | Practice or revision | easy | — |

### Subqueries · `sql.subqueries`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_sql_subqueries@1` | Practice or revision | easy | — |

### NULL and three-valued logic · `sql.null`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_lean_select_null_filter@1` | Practice or revision | easy | — |

### Functional dependencies and closure · `normalization.fds`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_lean_fds_counterexample@1` | Diagnostic only | easy | — |
| `q_lean_fds_closure@1` | Practice or revision | medium | — |

### Normal forms and anomalies · `normalization.normal_forms`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_lean_norm_checkpoint_depot@1` | Remediation checkpoints only | easy | NORM-03 checkpoint |
| `q_lean_norm_checkpoint_order@1` | Remediation checkpoints only | easy | NORM-03 checkpoint |
| `q_lean_norm_detector_registration@1` | Diagnostic only | easy | NORM-03 detector |
| `q_lean_norm_detector_branch@1` | Practice or revision | easy | NORM-03 detector |

### Lossless decomposition · `normalization.decomposition`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_normalization_decomposition@1` | Practice or revision | easy | — |

### ACID · `transactions.acid`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_transactions_acid@1` | Practice or revision | easy | — |

### Schedules and conflict serializability · `transactions.schedules`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_transactions_schedules@1` | Practice or revision | easy | — |

### Recoverability · `transactions.recoverability`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_transactions_recoverability@1` | Practice or revision | easy | — |

### Locks and two-phase locking · `concurrency.locks`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_concurrency_locks@1` | Practice or revision | easy | — |

### Deadlocks · `concurrency.deadlocks`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_concurrency_deadlocks@1` | Practice or revision | easy | — |

### Isolation anomalies · `concurrency.isolation`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_concurrency_isolation@1` | Practice or revision | easy | — |

### Clustered, nonclustered, dense and sparse indexes · `indexing.layout`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_indexing_layout@1` | Practice or revision | easy | — |

### Tree and hash indexes · `indexing.structures`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_indexing_structures@1` | Practice or revision | easy | — |

### Basic query plans · `indexing.plans`

| Version | Pool and activity | Difficulty | Misconception role |
|---|---|---|---|
| `q_topic_intro_indexing_plans@1` | Practice or revision | easy | — |

## Capacity and exact shortages

E/M/H columns give easy, medium and hard MCQs. The ordinary practice column excludes detector items. The next column counts both kinds of detector. Remaining is unopened practice after a learner completes the first targeted five-question practice (or fewer when the topic is smaller). A completed fresh general diagnostic also leaves zero currently authored diagnostic items. The gap proposes enough original **ordinary** questions for at least two per difficulty, while preserving each detector’s purpose and reserving checkpoints. The final column lists published SQL exercises.

| Topic | All E/M/H | Ordinary E/M/H | Diagnostic | Detectors | Checkpoints | Remaining | Add E/M/H | SQL |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `er.entities` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `er.cardinality` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `er.weak_entities` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `relational.relations` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `relational.keys` | 8/1/0 | 4/1/0 | 1 | 2 | 2 | 1 | 0/1/2 | — |
| `relational.algebra` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `sql.select` | 4/0/0 | 4/0/0 | 0 | 0 | 0 | 0 | 0/2/2 | — |
| `sql.ordering` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | `sql_sorted_customers@1` easy |
| `sql.joins` | 5/1/0 | 1/1/0 | 1 | 2 | 2 | 0 | 1/1/2 | `sql_matched_customers@1` medium, `sql_customers_without_orders@1` easy, `sql_join_001@1` easy |
| `sql.aggregation` | 3/0/0 | 3/0/0 | 0 | 0 | 0 | 0 | 0/2/2 | `sql_repeat_customers@1` medium |
| `sql.subqueries` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `sql.null` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | `sql_unassigned_orders@1` easy |
| `normalization.fds` | 1/1/0 | 0/1/0 | 1 | 0 | 0 | 0 | 2/1/2 | — |
| `normalization.normal_forms` | 4/0/0 | 0/0/0 | 1 | 2 | 2 | 0 | 2/2/2 | — |
| `normalization.decomposition` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `transactions.acid` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `transactions.schedules` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `transactions.recoverability` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `concurrency.locks` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `concurrency.deadlocks` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `concurrency.isolation` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `indexing.layout` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `indexing.structures` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |
| `indexing.plans` | 1/0/0 | 1/0/0 | 0 | 0 | 0 | 0 | 1/2/2 | — |

No topic can show a full easy → medium → hard progression with the current authored MCQs. The stated two-per-tier baseline needs **116** additional ordinary items (23 easy, 45 medium and 48 hard). The cheapest focused demonstration is relational keys, which already has four ordinary easy items and one ordinary medium item. Add one medium and two hard keys questions after independent factual and educational review. Separately, a balanced baseline screening with one item per domain would require new ER, transactions, concurrency and indexing diagnostics.

## Why Tickets and Accounts was missing

The unversioned ID is `q_keys_detector_tickets`. It is an easy diagnostic in `relational.keys`, and grading its mapped distractor can supply a KEYS-02 signal. The paired practice detector is `q_keys_detector_members@1`. Neither equivalent-looking practice questions nor a second pass through the ticket question should add another independent detector signal.

The existing regular database contains one account with a `possible` KEYS-02 record. A read-only aggregate check found a graded attempt for the ticket question on that account. No identities or answer content were needed for the check. The question existed in both databases with the correct version and topic. Ordinary Practice cannot select it. New Diagnostic excludes a previously allocated logical question, and a previously graded question cannot supply fresh evidence. Global screening is deterministic. A fresh account received Routes first and Tickets within the four-item screening. A fresh, exact keys diagnostic received Tickets as its only question.

A separate reproducible availability bug occurred when the general screening allocated Tickets and the learner paused before submitting it. The exact keys diagnostic used to exclude that already allocated item and reject its mixed parent session. The corrected Diagnostic view loads the keys items of the existing session by their original IDs, preserves that view across refresh, and leaves its other questions in the general screening. Once Tickets is graded, the targeted view correctly has zero remaining.

## Diagnostic and practice selection

Global diagnostic allocates up to 21 across domains, with no more than three per domain. The actual bank returns four questions from relational model, SQL and normalization. A subtopic diagnostic asks for up to three. Domain choices restrict allocation to their subtopics and balance across those subtopics. Practice targets five. An explicit difficulty is a filter for both resumption and allocation. In Chrome an open five-question easy keys session remained intact while medium opened a separate one-question session. The page disclosed the shortage, showed medium, and resumed the same medium item after refresh.

The initial scoped-allocation iteration passed 154 backend, two frontend and 11 Chrome scenarios, plus lint, types, build and strict validation. The authored Chrome scenario allocated a general screening, opened the keys diagnostic from the possible misconception, reloaded the targeted view, graded the reserved ticket and completed both remediation checkpoints.
