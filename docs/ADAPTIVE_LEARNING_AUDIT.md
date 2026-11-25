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

### Remaining capacity and recommended additions

The earlier two-per-tier column is an inventory floor. A new learner with two easy and two medium practice items alone would still have fewer than six independent answers, so the floor cannot guarantee entry to hard practice. A conservative standalone target for every topic is three easy, three medium and two hard ordinary items, requiring **161 additions** (44 easy, 69 medium and 48 hard), without counting SQL, detectors or diagnostics. This gives a successful learner enough independent evidence and room for one missed easy or medium answer before hard eligibility, subject to the mastery score. Smaller additions can work where independent diagnostics and suitable SQL are already available. The first useful addition is still one medium and two hard relational keys items. Then add one easy, one medium and two hard joins items alongside its existing diagnostic and SQL tasks. Prioritize different applications of each concept, such as diagnosing a multicolumn constraint or reasoning about matched and unmatched rows through a transformation. Include contrasting distractors with their own rationale. Every new published item requires original authored material, an exact factual reference and independent AI review under the existing policy. No items were added to the publication bank during this audit.

## What the learner model measures

The topic score starts at `0.50`. On a first graded logical item without an answer-revealing hint, it moves 20% of the distance toward `1` for correct or `0` for incorrect. Repeats, new versions of the same logical ID and a later unassisted attempt after an assisted first attempt add no new evidence; their grades and dates remain in attempt history. Evaluation answers are outside training evidence. The score is a bounded estimate. Confidence reflects the amount of independent evidence: fewer than three answers is insufficient, three to five is emerging, and six or more is supported. The low band ends at `0.40`; the high band starts at `0.70`.

Tier advancement uses independent correct answers on diagnostic, practice or revision MCQs. Medium requires two correct easy responses, at least emerging confidence and a score above `0.40`. Hard requires the easy evidence, two correct medium responses, supported confidence and a score at least `0.70`. Checkpoints and SQL can add first-answer evidence to the topic score. The MCQ tier-success counts stay separate, as does the misconception status. Advancement with a claim of sufficient performance additionally requires at least two distinct correct answers at the highest authored practice tier and the corresponding confidence. A sparse bank can instead lead to exploration, with the reason stating that fresh practice is unavailable. The review clock remains independent, with intervals of 1, 3, 7 and 14 days and reset on an independent missed review.

### Recommendation decision matrix

| Learner state | Actual decision and reason | Available activity and result |
|---|---|---|
| New account | Start diagnostic from Dashboard | Chrome opened the four eligible screening items for the three represented domains. The learner can browse the curriculum and other topics stay unassessed. |
| Weak recent performance | `RETEACH` · `NEEDS_REVIEW` | A wrong Tickets answer hit `0.400` and opened the reviewed keys lesson. The lesson offers fresh easy practice when available. |
| Two independent detector mistakes | `MISCONCEPTION_REMEDIATION` · `INDEPENDENT_MISCONCEPTION_EVIDENCE` | Tickets and Members produced an active KEYS-02; one answer produced only a possible state. |
| Remediation opened | Retain the targeted remediation and link to checkpoints | Two reserved, previously unseen items were allocated. Refresh preserves the allocated work. |
| Both checkpoints passed | Return to suitable available work | KEYS-02 became resolved after badges and rooms. Next action was fresh easy practice while medium evidence remained insufficient. |
| Checkpoint failure and exhausted bank | `RETEACH` · `CHECKPOINTS_EXHAUSTED` | One wrong and one correct retained an unresolved improving state and offered the reviewed lesson, with no fabricated extra checkpoints. |
| Easy competence | Exact fresh medium if present | The authored keys account had `0.744` on three first correct items and could open the medium superkey item. |
| Medium competence | Exact fresh hard if present | Isolated synthetic learner reached `0.701` and six independent answers including two medium successes. That rule cannot introduce hard items into the authored bank. |
| Hard mistake | Offer fresh practice at the tier supported by remaining evidence | A synthetic hard error lowered `0.701` to `0.561` while confidence stayed supported. Medium practice and then hard were offered. When medium errors provide zero medium successes, the policy cannot promote to hard. |
| Strong hard performance | `ADVANCE_TOPIC` or eligible due review | Two independent hard successes took the synthetic learner to `0.820` and the cardinality lesson. The review regression also verified due work can be recommended without another submission. |
| Topic ready with unassessed prerequisite | `LEARN` · `PREREQUISITE` when a prerequisite lesson exists | Policy regression sent a strong SELECT learner to relations before advancing. An unassessed prerequisite does not prevent explaining an active misconception. |
| No more suitable new items in the current topic | An exact unattempted SQL exercise when eligible, otherwise `EXPLORE_NEXT_TOPIC` | The authored keys learner had exhausted all six ordinary/detector practice items after the diagnostic and went to the entities lesson. No fresh-key exercise or mastery claim was invented. |
| Repeat or repeat after revealing help | Retain score, confidence and misconception independence | The singleton entities item stayed at `0.600` and one independent answer after four correct repeats. An assisted first answer and its unassisted repeat both left score at `0.500` and coverage at zero. |
| Several weak topics | Check prerequisites and activity eligibility, then rank by weakness, recency and curriculum order | This ordering was inspected in the backend. A multiple-weak-topic ranking journey was not independently authored in Chrome. |
| Several mastered topics | Skip candidates already ready unless they have an eligible diagnostic or SQL task; consider lower-evidence eligible topics | Availability and priority were inspected in the backend. A full multi-topic mastery browser replay was not possible with this bank. |
| All eligible material completed | `REVIEW_LATER` · `REVIEW_NO_FRESH_ITEMS`, or `COMPLETE` | The policy offers Progress for optional revision when due or opens the curriculum with a coverage explanation. Idle time alone leaves the score unchanged. |
| No eligible activities for the focus | `COMPLETE` · `NO_ELIGIBLE_CONTENT` | Unit test verified the explicit reason. Dashboard completion goes to Learn. |

## Replayed learner trajectories

Tests allocated actual versioned items, submitted through the deterministic grading service, and compared the decision returned by grading with the live recommendation read. The Chrome tests used separate signed-in synthetic accounts in disposable local databases, with the authored content and normal Vite, FastAPI and SQLite stack. Learner B alone used additional synthetic tiers. This audit measured application behavior. Human learning gains were outside its scope.

| Learner | Observed inputs and outcome | Eligible follow-through |
|---|---|---|
| A · struggling beginner | Wrong Tickets then wrong Members. Status moved from `possible` to `active`. Badge wrong, room correct. Final `0.405`, four independent, emerging, `improving`. | The reviewed foreign-key multiplicity lesson opened, then two reserved checkpoints. With no unseen checkpoint left, the learner returned to reteaching. |
| B · improving | On isolated synthetic ER items, alternated wrong/right at easy, succeeded at medium, made a hard mistake, then improved through more medium and hard items. Final `0.820`, 11 independent, supported, no misconception. | Exact fresh tiers opened in order. After the hard mistake, medium remained available. After two hard successes the next link opened the cardinality lesson. |
| C · strong | Passed Tickets, five fresh easy keys practice items and the medium superkey. Final `0.895`, seven independent, supported, no misconception. | Medium appeared after independent easy evidence. After the final medium, the next link opened the entities lesson with a content-exhaustion explanation. |
| D · repeating | Passed the one authored entities question, then passed it four more times. `0.600`, one independent, insufficient. A separate assisted-first repeat stayed at `0.500`, zero independent. | Repeat grades remained visible. No new confidence or detector signal was credited. Chrome checked the displayed score, evidence and two separate correct attempt entries. |
| E · exhausted | Completed the one fresh ordinary entities MCQ. A fresh-only request found no eligible item even though voluntary repeat practice remained possible. | The next action opened the reviewed cardinality lesson. Chrome checked this in the repeat and exhaustion journey. |
| F · misconception recovery | Wrong Members and Tickets, correct badges and rooms. Final `0.565`, four independent, emerging. Misconception progressed `possible` → `active` → `improving` → `resolved`. | Chrome reached both unseen checkpoints from a paused screening, then Progress showed resolution after navigation and reload. Another keys diagnostic honestly reported no fresh questions. |

The rows below retain the step-by-step scores and question IDs from the replay. `score/count` means the topic score and independent answer count. Option positions are zero-based as stored in SQLite. Right and wrong identify the submitted key or distractor. Rows without a misconception status had no associated signal. Scores are rounded for display.

**A · Beginner**

```text
diagnostic:q_keys_detector_tickets@1 option 1 wrong 0.500/0 → 0.400/1 insufficient possible RETEACH:relational.keys NEEDS_REVIEW
practice:q_keys_detector_members@1 option 3 wrong 0.400/1 → 0.320/2 insufficient active MISCONCEPTION_REMEDIATION:relational.keys INDEPENDENT_MISCONCEPTION_EVIDENCE
checkpoint:q_keys_checkpoint_badges@1 option 0 wrong 0.320/2 → 0.256/3 emerging active MISCONCEPTION_REMEDIATION:relational.keys INDEPENDENT_MISCONCEPTION_EVIDENCE
checkpoint:q_keys_checkpoint_rooms@1 option 1 right 0.256/3 → 0.405/4 emerging improving RETEACH:relational.keys CHECKPOINTS_EXHAUSTED
```

**B · Improving, isolated tiers**

```text
practice:audit_easy_0@1 option 1 wrong 0.500/0 → 0.400/1 insufficient — RETEACH:er.entities NEEDS_REVIEW
practice:audit_easy_1@1 option 0 right 0.400/1 → 0.520/2 insufficient — PRACTICE_EASY:er.entities TARGETED_PRACTICE
practice:audit_easy_2@1 option 1 wrong 0.520/2 → 0.416/3 emerging — PRACTICE_EASY:er.entities TARGETED_PRACTICE
practice:audit_easy_3@1 option 0 right 0.416/3 → 0.533/4 emerging — PRACTICE_MEDIUM:er.entities TARGETED_PRACTICE
practice:audit_medium_0@1 option 0 right 0.533/4 → 0.626/5 emerging — PRACTICE_MEDIUM:er.entities TARGETED_PRACTICE
practice:audit_medium_1@1 option 0 right 0.626/5 → 0.701/6 supported — PRACTICE_HARD:er.entities TARGETED_PRACTICE
practice:audit_hard_0@1 option 1 wrong 0.701/6 → 0.561/7 supported — PRACTICE_MEDIUM:er.entities TARGETED_PRACTICE
practice:audit_medium_2@1 option 0 right 0.561/7 → 0.649/8 supported — PRACTICE_MEDIUM:er.entities TARGETED_PRACTICE
practice:audit_medium_3@1 option 0 right 0.649/8 → 0.719/9 supported — PRACTICE_HARD:er.entities TARGETED_PRACTICE
practice:audit_hard_1@1 option 0 right 0.719/9 → 0.775/10 supported — PRACTICE_HARD:er.entities TARGETED_PRACTICE
practice:audit_hard_2@1 option 0 right 0.775/10 → 0.820/11 supported — LEARN:er.cardinality ADVANCE_TOPIC
```

**C · Strong authored learner**

```text
diagnostic:q_keys_detector_tickets@1 option 0 right 0.500/0 → 0.600/1 insufficient — PRACTICE_EASY:relational.keys TARGETED_PRACTICE
practice:q_keys_detector_members@1 option 2 right 0.600/1 → 0.680/2 insufficient — PRACTICE_EASY:relational.keys TARGETED_PRACTICE
practice:q_lean_keys_candidate_count@1 option 3 right 0.680/2 → 0.744/3 emerging — PRACTICE_MEDIUM:relational.keys TARGETED_PRACTICE
practice:q_lean_keys_composite@1 option 2 right 0.744/3 → 0.795/4 emerging — PRACTICE_MEDIUM:relational.keys TARGETED_PRACTICE
practice:q_lean_keys_fk_target@1 option 0 right 0.795/4 → 0.836/5 emerging — PRACTICE_MEDIUM:relational.keys TARGETED_PRACTICE
practice:q_practice_keys_missing@1 option 1 right 0.836/5 → 0.869/6 supported — PRACTICE_MEDIUM:relational.keys TARGETED_PRACTICE
practice:q_lean_keys_superkey@1 option 1 right 0.869/6 → 0.895/7 supported — LEARN:er.entities EXPLORE_NEXT_TOPIC
```

**D/E · Repeats and exhaustion**

```text
practice:q_topic_intro_er_entities@1 option 1 right 0.500/0 → 0.600/1 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
practice:q_topic_intro_er_entities@1 option 1 right 0.600/1 → 0.600/1 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
practice:q_topic_intro_er_entities@1 option 1 right 0.600/1 → 0.600/1 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
practice:q_topic_intro_er_entities@1 option 1 right 0.600/1 → 0.600/1 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
practice:q_topic_intro_er_entities@1 option 1 right 0.600/1 → 0.600/1 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
practice:q_topic_intro_er_entities@1 option 1 right 0.500/0 → 0.500/0 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
practice:q_topic_intro_er_entities@1 option 1 right 0.500/0 → 0.500/0 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
```

**F · Recovery**

```text
practice:q_keys_detector_members@1 option 3 wrong 0.500/0 → 0.400/1 insufficient possible RETEACH:relational.keys NEEDS_REVIEW
diagnostic:q_keys_detector_tickets@1 option 1 wrong 0.400/1 → 0.320/2 insufficient active MISCONCEPTION_REMEDIATION:relational.keys INDEPENDENT_MISCONCEPTION_EVIDENCE
checkpoint:q_keys_checkpoint_badges@1 option 3 right 0.320/2 → 0.456/3 emerging improving MISCONCEPTION_REMEDIATION:relational.keys INDEPENDENT_MISCONCEPTION_EVIDENCE
checkpoint:q_keys_checkpoint_rooms@1 option 1 right 0.456/3 → 0.565/4 emerging resolved PRACTICE_EASY:relational.keys TARGETED_PRACTICE
```

**Migration regression**

```text
practice:q_topic_intro_er_entities@1 option 1 right 0.500/0 → 0.600/1 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
practice:q_topic_intro_er_entities@1 option 1 right 0.600/1 → 0.600/1 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
practice:q_topic_intro_er_entities@1 option 1 right 0.600/1 → 0.600/1 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
practice:q_topic_intro_er_entities@1 option 1 right 0.600/1 → 0.600/1 insufficient — LEARN:er.cardinality EXPLORE_NEXT_TOPIC
```

**Review regression**

```text
diagnostic:q_keys_detector_tickets@1 option 0 right 0.500/0 → 0.600/1 insufficient — PRACTICE_EASY:relational.keys TARGETED_PRACTICE
```

## Defects verified and corrected

| Severity | Reproduction | Correction and regression |
|---|---|---|
| P2 | An ungraded item allocated in the general screening was unavailable from a narrower diagnostic link. | Resume eligible items within the original session and preserve the selected scope across refresh. Backend and signed-in Chrome verified that the ticket grades once and does not recur as fresh. |
| P2 | Requesting medium practice could resume easy work or insert wrong-tier filler. | Filter both allocation and resumption by scope and difficulty. Show the actual size. Backend and Chrome verified a separate one-item medium session beside the existing easy session. |
| P2 | Graded repeats could raise the mastery score; a later unassisted replay could add confidence after revealing help. | Count score/confidence only on the independent first answer. Migration 0008 preserves attempts, decision history and review dates. Backend and Chrome verified the projected score and visible repeat history. |
| P2 | Static recommendations could keep suggesting used practice, ignore a newly due review or pick a different SQL exercise than the one available. | Recompute availability on read, offer fresh exact tiers and identify the eligible SQL exercise by ID. Tests cover review becoming due, exhaustion and the exact SQL ID. |
| P2 | After a foreign-key detector answer or failed checkpoint, generic keys reteaching could open a lesson about candidate-key minimality. | Use the reviewed lesson for the matching pattern when reteaching, including after checkpoints run out. A Chrome failure reproduced the mismatch. The regression requires the foreign-key multiplicity lesson and verifies its fresh-practice link. |
| P3 | Creates within the same second could choose an older decision or display an older attempt first. | Use append order to break ties. The progression sequences repeatedly verify the live recommendation against the latest graded result. |

No unresolved P0 or P1 finding was identified in this progression audit. Earlier platform acceptance remains separately documented. The bank shortages limit how much of the policy a learner can exercise on authored content.

## Validation and Chrome evidence

Run these from the repository root using the documented local environment. Chrome used the installed Google Chrome channel, default browser controls, real answer routes and disposable databases. The signed-in tests did not use the demo account or mocked grades. A deliberate browser delay in one test exercised the pending state, then continued to the actual backend.

| Command or evidence | Observed result |
|---|---|
| `bash scripts/check_backend.sh backend/.venv/bin` | 163 pytest cases passed, plus Ruff, mypy and strict content validation. |
| `backend/.venv/bin/python -m pytest -q -s backend/tests/test_progression.py` | 14 cases passed. Allocations, scores, recommendation parity and migration/review cases are replayed above. The additional SQL test verifies the exact recommendation and resumption even with another exercise open. Worker availability is varied in the policy test; the actual worker is covered separately. |
| `backend/.venv/bin/python scripts/validate_content.py --strict --stage S1 --review-policy learner` and the S4 equivalent | Both passed. Counts were 46 MCQs, 33 ordinary practice MCQs, 22 lessons, six SQL tasks and three enabled misconceptions. Separate human review count was zero. |
| `npm --prefix frontend run lint`, `npm --prefix frontend run typecheck`, `npm --prefix frontend run build`, `npm --prefix frontend test` | All passed, including two Vitest tests. |
| `DBMS_TEST_CHROME=1 npm --prefix frontend run test:e2e` | Four ordinary smoke/regression scenarios passed. Opt-in authored and progression cases ran separately. |
| `DBMS_TEST_AUTHORED=1 DBMS_TEST_CHROME=1 npm --prefix frontend run test:e2e -- authored-demo.spec.ts` | Ten authored scenarios cover the signed-in group and difficulty controls, separate easy and medium sessions, abandoned general diagnostic and ticket resumption, one-question shortage, follow-through to lessons/practice, two different checkpoint outcomes, exhaustion, refresh, and the dedicated A/B replay. |
| `DBMS_TEST_AUTHORED=1 DBMS_TEST_PROGRESSION=1 DBMS_TEST_CHROME=1 npm --prefix frontend run test:e2e -- progression.spec.ts` | One additional signed-in learner tests the full easy → medium → hard link flow on isolated synthetic tiers, including a hard error, refresh and recovery before opening the next lesson. |
| `backend/.venv/bin/python scripts/verify_demo.py` | Authored CLI replay passed, with contrasting misconceptions, checkpoint resolution and SQL grading. |
| `backend/.venv/bin/python -m pytest -q backend/tests/test_educational_sql.py backend/tests/test_sql_worker.py` | 33 passed. The six task reference and alternate SELECTs matched independently calculated fixture expectations. The restricted worker accepted alternate solutions and rejected the tested incorrect variants. |
| `backend/.venv/bin/python -m alembic -c backend/alembic.ini current`, the demo variant `-x demo=true current`, and `alembic check` | Both local databases at `0008_independent_mastery`; no schema drift or FK violations. The app retained 39 attempts, 39 history entries, one misconception and 52 question versions. Demo retained 1, 1, 0 and 52 respectively. |
| `backend/.venv/bin/python scripts/check_ollama.py` and `--book` | Both passed against existing `qwen3:1.7b`. The model explained LEFT JOIN and ON DELETE CASCADE with actual retrieved citations. |


GitHub Actions verified the substantive allocation and progression iterations on `main`, including both backend and frontend jobs. Chrome, the Apple Silicon SQL worker and real Ollama were verified locally. [Allocation workflow](https://github.com/Aadit5gupta/adaptive-dbms-tutor/actions/runs/45558334251) · [Progression workflow](https://github.com/Aadit5gupta/adaptive-dbms-tutor/actions/runs/45561354252)

## Verdict

**CONDITIONAL PASS.** The scoped assessment flows, evidence-backed remediation, recommendation links and sparse-bank fallbacks were verified in signed-in Chrome with authored items. The full tier policy works with isolated synthetic fixtures. The 46 authored MCQs cover introductory practice much better than screening or advanced assessment. Only three subtopics have medium MCQs, there are no hard or held-out items, and four domains have no diagnostic items. Human-only approval and broader study efficacy are still outstanding. A local demo can show successful progression through available keys content and independent misconception recovery. A demonstration of authored hard questions requires the reviewed additions above.
