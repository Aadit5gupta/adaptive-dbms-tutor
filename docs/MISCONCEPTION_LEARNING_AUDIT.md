# Misconception-aware learning audit

**25 November 2026** · Baseline `7ecc659`

## Coverage before and after

The [adaptive learning audit](ADAPTIVE_LEARNING_AUDIT.md) established the baseline. This phase adds 30 versioned original practice MCQs in seven subtopics. Three are mapped detectors and 27 are ordinary practice. Each supported misconception now has two practice detectors and one diagnostic detector. The four diagnostics, six reserved checkpoints, 22 original lessons and six SQL tasks retain their prior roles and versions.

| Subtopic | All MCQs before → after, E/M/H | Practice including detectors before → after, E/M/H | Diagnostics | Reserved checkpoints |
|---|---|---|---:|---:|
| Candidate, primary and foreign keys | 8/1/0 → 9/3/3 | 5/1/0 → 6/3/3 | 1 | 2 |
| INNER and LEFT JOIN | 5/1/0 → 7/2/2 | 2/1/0 → 4/2/2 | 1 | 2 |
| Aggregates, GROUP BY and HAVING | 3/0/0 → 3/2/2 | 3/0/0 → 3/2/2 | 0 | 0 |
| Functional dependencies and closure | 1/1/0 → 2/3/0 | 0/1/0 → 1/3/0 | 1 | 0 |
| Normal forms and anomalies | 4/0/0 → 8/3/2 | 1/0/0 → 5/3/2 | 1 | 2 |
| NULL and three-valued logic | 1/0/0 → 2/1/0 | 1/0/0 → 2/1/0 | 0 | 0 |
| SELECT and WHERE | 4/0/0 → 4/1/0 | 4/0/0 → 4/1/0 | 0 | 0 |
| **Entire bank** | **43/3/0 → 52/15/9** | **33/3/0 → 42/15/9** | **4** | **6** |

New practice on Keys ranges from scoping uniqueness to a bay within a station to validating a composite reference against a separate uniqueness rule. JOIN practice covers result multiplicity, a counterexample to INNER/LEFT equivalence, filtering in ON versus WHERE, distinguishing nullable values from NULL-extended rows, and repairing the join condition in a chain. Normal Forms now has eight ordinary practice items across all three tiers, including anomaly recognition, failure analysis, 3NF versus BCNF, and a dependency-preserving lossless split.

## Verification and source evidence

The primary reviewer wrote the questions as drafts, solved each and checked the controlling facts. Two separate-context AI reviewers received only their assigned stems, options, factual references and proposed signal positions. They solved before seeing the authored answer keys. Every independently returned key matched the final draft. One reviewer checked the 18 constraint and SQL items, recreated outputs with benign in-memory SQLite fixtures, and tested all four alternatives to the revised hard JOIN. The other checked 12 normalization items with functional-dependency closure, candidate-key, BCNF and lossless-join reasoning. Both compared new detectors with existing questions, lessons and checkpoints. Source checks used the publisher chapters and their published headings. Direct automated HTML fetches from the workstation returned HTTP 403, so the stored links use the verified chapter URLs and the section names below identify the precise material.

Reviewer IDs are `ai:codex_misconception_primary`, `ai:codex_sql_question_review` and `ai:codex_normalization_question_review`. All 30 dispositions are `ai_verified`, with `@1` new logical IDs. The examples, data and wording are original. Book citations establish provenance for the facts. The rights manifest and indexed textbook scopes were unchanged.

| Source and section | Fact checked |
|---|---|
| Runestone §1.7.4–1.7.5.1 | Parent key uniqueness, complete composite tuple matches, cascading updates, scope of UNIQUE. [Keys and constraints](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/07-constraints/constraints.html) |
| Runestone §1.4.2 and §1.4.6 | Matched row pairs, outer join NULL extension, and preserving dependent joins. [Queries on multiple tables](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/04-multiple-tables/multiple-tables.html) |
| Runestone §1.9.2 and §1.9.3.1 | COUNT of rows versus values, and WHERE before grouping and HAVING after grouping. [Grouping and aggregation](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/09-grouping-and-aggregation/grouping-and-aggregation.html) |
| Runestone §1.3.4.4 and §1.3.5 | Boolean combinations, comparisons with NULL, and three-valued logic. [Expressions](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/03-expressions/expressions.html) |
| Runestone §3.3 normalization, including modification anomalies, closure, normal forms, decomposition and its properties | Complete determinants, minimal candidate keys, proper subsets, dependency chains, BCNF and lossless decomposition. [Normalization](https://runestone.academy/ns/books/published/practical_db/PART3_RELATIONAL_DATABASE_THEORY/03-normalization/normalization.html) |
| SQLite documentation | Cross-check for composite NULL, matching unique parent indexes, FK actions, ON/WHERE processing, and empty-input SUM. [Foreign keys](https://www.sqlite.org/foreignkeys.html#fk_composite) · [SELECT](https://www.sqlite.org/lang_select.html) · [Aggregate functions](https://www.sqlite.org/lang_aggfunc.html) · [Expressions](https://www.sqlite.org/lang_expr.html) |
| Database System Concepts, Chapter 7 | Cross-check for formal 3NF's prime attribute exception, closure, and lossless and dependency-preserving decomposition. [Authors' slides](https://db-book.com/slides-dir/PDF-dir/ch7.pdf) |

Independent keys and the controlling facts are below. The key and signal positions are zero-based. All items are from the practice pool. A mapped distractor is evidence only when selected on a first eligible attempt.

| Version | Tier | Key | Mapped option | Control check |
|---|---|---:|---|---|
| `q_lean_keys_migrate_children@1` | easy | 1 | `KEYS-02` · 0 | The station and bay pair enforces local exclusivity. A scanner ID is already unique. |
| `q_lean_keys_alternate_parent@1` | medium | 2 | — | Enforce uniqueness on the referenced column. The existing data and an ordinary index are insufficient. |
| `q_lean_keys_cascaded_code@1` | medium | 0 | — | An update cascades to both repairs and preserves those rows. |
| `q_lean_keys_composite_fk_pair@1` | hard | 3 | — | Each child tuple must match one parent row. Matching two different parent rows fails. |
| `q_lean_keys_composite_unique_scope@1` | hard | 1 | — | P duplicates shop and day, R has no parent tuple, and Q passes both constraints. |
| `q_lean_keys_composite_null_rule@1` | hard | 2 | — | SQLite accepts a NULL in either child component. Only the two non-NULL values require a full parent match. |
| `q_join_practice_duplicate_matches@1` | easy | 2 | — | Projection keeps both matched row pairs without DISTINCT. |
| `q_join_practice_preservation_claim@1` | easy | 3 | `SQL-JOIN-01` · 0 | Adding a machine with no reading distinguishes the two queries. The signal explicitly attributes NULL padding to INNER JOIN. |
| `q_join_practice_right_side_filter@1` | medium | 3 | — | A right-side eligibility test in ON preserves workshops with no eligible match. |
| `q_join_practice_matched_nullable_value@1` | hard | 0 | — | A NULL note can be stored in a real booking. Only unmatched rooms have a NULL booking ID. |
| `q_join_practice_preserve_two_stages@1` | hard | 0 | — | Match the port to the rack ID. Both LEFT JOINs preserve missing children. |
| `q_progress_agg_filter_order@1` | medium | 1 | — | WHERE removes the low readings before counting, then HAVING keeps only B with two. |
| `q_progress_agg_distinct_nonnull@1` | medium | 3 | — | Four rows, three non-NULL occurrences and two different non-NULL values. |
| `q_progress_agg_multiplication_before_sum@1` | hard | 0 | — | Two charges each appear three times. Aggregate charges first, and use the case total once. |
| `q_progress_agg_empty_group_vs_null@1` | hard | 2 | — | Both sites survive. The non-NULL child IDs count 1 and 0, and both SUM expressions return NULL. |
| `q_norm_practice_atomic_cell@1` | easy | 1 | — | Separate association rows represent any number of addresses without multi-valued cells. |
| `q_norm_practice_anomaly_update@1` | easy | 2 | — | Editing one copy of a repeated office phone fact is an update anomaly. |
| `q_norm_practice_full_dependency@1` | easy | 0 | — | Neither proper key subset determines the price, and the stem excludes non-key determinants. |
| `q_norm_practice_calibration_confusion@1` | easy | 2 | `NORM-03` · 0 | Lab ID has a proper-subset determinant. Procedure note uses a non-key intermediary. Only the explicitly swapped diagnosis is mapped. |
| `q_norm_practice_split_partial@1` | medium | 0 | — | The new composite key still permits inconsistent per-tool limits in different weeks. |
| `q_norm_practice_split_transitive@1` | medium | 1 | — | Each immediate determinant gets its own relation, with joins on device and model IDs. |
| `q_norm_practice_qualify_normal_form@1` | medium | 3 | — | The single-column key rules out the given partial-dependency case. The non-key determinant violates 3NF. |
| `q_norm_practice_bcnf_counterexample@1` | hard | 2 | — | Lab is prime, satisfying 3NF, but supervisor does not determine trainee and violates BCNF. |
| `q_norm_practice_lossless_bcnf_choice@1` | hard | 0 | — | M determines the shared component, D and M are local keys, and the original dependencies are local. |
| `q_progress_fds_combine_determinant@1` | easy | 1 | — | Both columns must agree before different prices contradict the FD. |
| `q_progress_fds_closure_missing@1` | medium | 3 | — | A derives B then C. E also needs D, which remains outside the closure. |
| `q_progress_fds_alternate_keys@1` | medium | 0 | — | C is mandatory. Either A or B derives the other and then D together with C. |
| `q_progress_null_zero_or_missing@1` | easy | 2 | — | IS NULL selects the missing reading. Zero is an existing value. |
| `q_progress_null_or_unknown@1` | medium | 2 | — | True OR unknown passes; false OR unknown does not. IDs 1 and 3 pass. |
| `q_progress_select_boolean_groups@1` | medium | 1 | — | Require urgency and group the two allowed kinds under the same condition. |

The first JOIN draft repeated the existing order prediction too closely. The final prompt asks for a future data change that separates two currently equivalent outputs. The first normalization draft merely classified another partial dependency. The final Calibration prompt contrasts a proper subset with a non-key intermediate determinant in the same schema. The initial hard JOIN compared chained join types like the source example, so the final item instead diagnoses a wrong ON key. The medium Hire question tests residual redundancy in a flawed split. It does not teach the exact answer to the reserved split-selection checkpoint.

## Detectors, remediation and unseen transfer

| Pattern | Practice opportunities | Diagnostic opportunity | Lesson and two reserved checkpoints |
|---|---|---|---|
| KEYS-02 | `q_keys_detector_members@1` checks an existing repeated child reference. `q_lean_keys_migrate_children@1` tests choosing the correct scope of a uniqueness constraint. | `q_keys_detector_tickets@1` | `lesson_fk_multiplicity@1`. `q_keys_checkpoint_badges@1` evaluates NULL, a valid repeated reference and an invalid parent. `q_keys_checkpoint_rooms@1` checks the effect of adding child uniqueness. |
| SQL-JOIN-01 | `q_join_detector_orders@1` predicts the result for an unmatched buyer. `q_join_practice_preservation_claim@1` asks for a counterexample to equivalence. | `q_join_detector_routes@1` | `lesson_join_unmatched@1`. `q_join_checkpoint_households@1` transfers to LEFT output shape. `q_join_checkpoint_teams@1` applies row preservation when computing a grouped count. |
| NORM-03 | `q_lean_norm_detector_branch@1` classifies a dependency through another non-key attribute on a single-column key. `q_norm_practice_calibration_confusion@1` contrasts two dependency types within a composite-key schema. | `q_lean_norm_detector_registration@1` | `lesson_dependency_chain@1`. `q_lean_norm_checkpoint_depot@1` identifies the intermediary. `q_lean_norm_checkpoint_order@1` identifies the appropriate split for a partial dependency. |

Mapped choices cite a specific wrong rule. A mistake in an unrelated option updates the grade but contributes no signal. Stronger help can disqualify evidence. The first mapped mistake is possible evidence; the second on a different logical question can activate the hypothesis. The existing engine then requires two correct fresh reserved checkpoint answers to resolve. This phase left grade calculation, misconception thresholds and adaptive rules intact.

## Learn-to-Practice entry point

Chrome reproduced the lesson button landing on **Any difficulty**, even for a fresh learner reading a foundational lesson. With the new mixed-tier bank, Keys' old allocation order would put two medium items before the second easy detector and leave it outside the first five. Learn now starts at the lowest published practice tier for the topic. The catalog gets that tier from current MCQ versions. The dropdown remains editable and a lesson reached from a recommendation preserves its explicit fresh level. No special detector weighting or forced diagnostic was introduced. Exact-topic sessions still prioritize unseen eligible items.

## Remaining shortages

- Keys has six easy, three medium and three hard practice items, enough for the verified progression and recovery after a hard error. Joins and Normal Forms have enough first-attempt MCQs for a clean progression but only two hard items each. A hard miss can leave too little unseen hard evidence to demonstrate the same outcome.
- Aggregation has three easy, two medium and two hard MCQs. There are only five pre-hard MCQs, so one independent SQL grade (available where the worker is supported) or another suitable independent item is necessary to meet supported confidence. A full aggregation progression was not replayed.
- FDs, NULL and SELECT lack hard items. NULL and SELECT each have only one medium item. The other 17 curriculum subtopics still rely on their introductory practice depth, and four curriculum domains still lack diagnostic items. No held-out assessment items were added.
- Each pattern has two reserved checkpoints. Spending a checkpoint on an unsuccessful attempt can exhaust the current recovery bank. The policy still offers reviewed reteaching. Future practice additions should keep detectors and checkpoints conceptually distinct.
- The three reviewed patterns cover specific errors in keys, joins and normalization. They cannot measure all misconceptions or establish human learning gains. No qualifying human-reviewed items are recorded.

## Observed Chrome learner journeys

Chrome used separate signed-in accounts and temporary SQLite databases populated from the reviewed source bank. The logged options use zero-based positions. The following are actual submitted answers, mastery changes, states and recommendation reasons returned by the application.

### keys

- Started practice with 5 allocated items. First item `q_keys_detector_members@1`.
- `q_keys_detector_members@1`, easy, option 3 (incorrect). Score 0.500 → 0.400, insufficient confidence. KEYS-02 possible with 1 signals. Recommendation `RETEACH` for `relational.keys`, Your recent answers suggest reviewing the concept before more practice.
- `q_lean_keys_candidate_count@1`, easy, option 3 (correct). Score 0.400 → 0.520, insufficient confidence. No misconception signal. Recommendation `DIAGNOSTIC` for `relational.keys`, A few more independent answers will help clarify what to practice.
- `q_lean_keys_composite@1`, easy, option 2 (correct). Score 0.520 → 0.616, emerging confidence. No misconception signal. Recommendation `PRACTICE_MEDIUM` for `relational.keys`, Try an available medium question to build evidence for this topic.
- `q_lean_keys_fk_target@1`, easy, option 0 (correct). Score 0.616 → 0.693, emerging confidence. No misconception signal. Recommendation `PRACTICE_MEDIUM` for `relational.keys`, Try an available medium question to build evidence for this topic.
- `q_lean_keys_migrate_children@1`, easy, option 0 (incorrect). Score 0.693 → 0.554, emerging confidence. KEYS-02 active with 2 signals. Recommendation `MISCONCEPTION_REMEDIATION` for `relational.keys`, Different answers suggest you may be applying this idea: Assumes repeated foreign-key values are invalid. Try a worked example and checkpoints.
- Followed `/learn/lesson_fk_multiplicity@1?checkpoints=1` and opened the destination.
- Started checkpoint with 2 allocated items. First item `q_keys_checkpoint_badges@1`.
- `q_keys_checkpoint_badges@1`, easy, option 3 (correct). Score 0.554 → 0.643, supported confidence. KEYS-02 improving with 2 signals. Recommendation `MISCONCEPTION_REMEDIATION` for `relational.keys`, Different answers suggest you may be applying this idea: Assumes repeated foreign-key values are invalid. Try a worked example and checkpoints.
- `q_keys_checkpoint_rooms@1`, easy, option 1 (correct). Score 0.643 → 0.715, supported confidence. KEYS-02 resolved with 2 signals. Recommendation `PRACTICE_MEDIUM` for `relational.keys`, Try an available medium question to build evidence for this topic.
- Progress showed 7 attempts, 7 independent responses and supported confidence.
- Followed `/practice?topic=relational.keys&difficulty=medium&fresh=1` and opened the destination.

### joins

- Started practice with 4 allocated items. First item `q_join_detector_orders@1`.
- `q_join_detector_orders@1`, easy, option 0 (incorrect). Score 0.500 → 0.400, insufficient confidence. SQL-JOIN-01 possible with 1 signals. Recommendation `RETEACH` for `sql.joins`, Your recent answers suggest reviewing the concept before more practice.
- `q_join_practice_duplicate_matches@1`, easy, option 2 (correct). Score 0.400 → 0.520, insufficient confidence. No misconception signal. Recommendation `DIAGNOSTIC` for `sql.joins`, A few more independent answers will help clarify what to practice.
- `q_join_practice_preservation_claim@1`, easy, option 0 (incorrect). Score 0.520 → 0.416, emerging confidence. SQL-JOIN-01 active with 2 signals. Recommendation `MISCONCEPTION_REMEDIATION` for `sql.joins`, Different answers suggest you may be applying this idea: Assumes INNER JOIN preserves unmatched rows. Try a worked example and checkpoints.
- Followed `/learn/lesson_join_unmatched@1?checkpoints=1` and opened the destination.
- Started checkpoint with 2 allocated items. First item `q_join_checkpoint_households@1`.
- `q_join_checkpoint_households@1`, easy, option 0 (correct). Score 0.416 → 0.533, emerging confidence. SQL-JOIN-01 improving with 2 signals. Recommendation `MISCONCEPTION_REMEDIATION` for `sql.joins`, Different answers suggest you may be applying this idea: Assumes INNER JOIN preserves unmatched rows. Try a worked example and checkpoints.
- `q_join_checkpoint_teams@1`, easy, option 3 (correct). Score 0.533 → 0.626, emerging confidence. SQL-JOIN-01 resolved with 2 signals. Recommendation `PRACTICE_EASY` for `sql.joins`, Try an available easy question to build evidence for this topic.
- Progress showed 5 attempts, 5 independent responses and emerging confidence.
- Followed `/practice?topic=sql.joins&difficulty=easy&fresh=1` and opened the destination.

### normal-forms

- Started practice with 5 allocated items. First item `q_lean_norm_detector_branch@1`.
- `q_lean_norm_detector_branch@1`, easy, option 0 (incorrect). Score 0.500 → 0.400, insufficient confidence. NORM-03 possible with 1 signals. Recommendation `RETEACH` for `normalization.normal_forms`, Your recent answers suggest reviewing the concept before more practice.
- `q_norm_practice_anomaly_update@1`, easy, option 2 (correct). Score 0.400 → 0.520, insufficient confidence. No misconception signal. Recommendation `DIAGNOSTIC` for `normalization.normal_forms`, A few more independent answers will help clarify what to practice.
- `q_norm_practice_atomic_cell@1`, easy, option 1 (correct). Score 0.520 → 0.616, emerging confidence. No misconception signal. Recommendation `PRACTICE_MEDIUM` for `normalization.normal_forms`, Try an available medium question to build evidence for this topic.
- `q_norm_practice_calibration_confusion@1`, easy, option 0 (incorrect). Score 0.616 → 0.493, emerging confidence. NORM-03 active with 2 signals. Recommendation `MISCONCEPTION_REMEDIATION` for `normalization.normal_forms`, Different answers suggest you may be applying this idea: Confuses partial and transitive dependencies. Try a worked example and checkpoints.
- Followed `/learn/lesson_dependency_chain@1?checkpoints=1` and opened the destination.
- Started checkpoint with 2 allocated items. First item `q_lean_norm_checkpoint_depot@1`.
- `q_lean_norm_checkpoint_depot@1`, easy, option 3 (correct). Score 0.493 → 0.594, emerging confidence. NORM-03 improving with 2 signals. Recommendation `MISCONCEPTION_REMEDIATION` for `normalization.normal_forms`, Different answers suggest you may be applying this idea: Confuses partial and transitive dependencies. Try a worked example and checkpoints.
- `q_lean_norm_checkpoint_order@1`, easy, option 0 (correct). Score 0.594 → 0.675, supported confidence. NORM-03 resolved with 2 signals. Recommendation `PRACTICE_MEDIUM` for `normalization.normal_forms`, Try an available medium question to build evidence for this topic.
- Progress showed 6 attempts, 6 independent responses and supported confidence.
- Followed `/practice?topic=normalization.normal_forms&difficulty=medium&fresh=1` and opened the destination.

### advancing

- Started practice with 1 allocated items. First item `q_topic_intro_relational_relations@1`.
- `q_topic_intro_relational_relations@1`, easy, option 2 (correct). Score 0.500 → 0.600, insufficient confidence. No misconception signal. Recommendation `LEARN` for `er.entities`, Fresh practice at a suitable level is unavailable here. Continue with Entities and attributes while this topic remains open for review.
- Started practice with 5 allocated items. First item `q_keys_detector_members@1`.
- `q_keys_detector_members@1`, easy, option 2 (correct). Score 0.500 → 0.600, insufficient confidence. No misconception signal. Recommendation `DIAGNOSTIC` for `relational.keys`, A few more independent answers will help clarify what to practice.
- `q_lean_keys_candidate_count@1`, easy, option 3 (correct). Score 0.600 → 0.680, insufficient confidence. No misconception signal. Recommendation `DIAGNOSTIC` for `relational.keys`, A few more independent answers will help clarify what to practice.
- `q_lean_keys_composite@1`, easy, option 2 (correct). Score 0.680 → 0.744, emerging confidence. No misconception signal. Recommendation `PRACTICE_MEDIUM` for `relational.keys`, Try an available medium question to build evidence for this topic.
- `q_lean_keys_fk_target@1`, easy, option 0 (correct). Score 0.744 → 0.795, emerging confidence. No misconception signal. Recommendation `PRACTICE_MEDIUM` for `relational.keys`, Try an available medium question to build evidence for this topic.
- Followed `/practice?topic=relational.keys&difficulty=medium&fresh=1` and opened the destination.
- Started practice with 3 allocated items. First item `q_lean_keys_alternate_parent@1`.
- `q_lean_keys_alternate_parent@1`, medium, option 2 (correct). Score 0.795 → 0.836, emerging confidence. No misconception signal. Recommendation `PRACTICE_MEDIUM` for `relational.keys`, Try an available medium question to build evidence for this topic.
- `q_lean_keys_cascaded_code@1`, medium, option 0 (correct). Score 0.836 → 0.869, supported confidence. No misconception signal. Recommendation `PRACTICE_HARD` for `relational.keys`, Try an available hard question to build evidence for this topic.
- Followed `/practice?topic=relational.keys&difficulty=hard&fresh=1` and opened the destination.
- Started practice with 3 allocated items. First item `q_lean_keys_composite_fk_pair@1`.
- `q_lean_keys_composite_fk_pair@1`, hard, option 0 (incorrect). Score 0.869 → 0.695, supported confidence. No misconception signal. Recommendation `PRACTICE_MEDIUM` for `relational.keys`, Try an available medium question to build evidence for this topic.
- Followed `/practice?topic=relational.keys&difficulty=medium&fresh=1` and opened the destination.
- Started practice with 3 allocated items. First item `q_lean_keys_superkey@1`.
- `q_lean_keys_superkey@1`, medium, option 1 (correct). Score 0.695 → 0.756, supported confidence. No misconception signal. Recommendation `PRACTICE_HARD` for `relational.keys`, Try an available hard question to build evidence for this topic.
- Followed `/practice?topic=relational.keys&difficulty=hard&fresh=1` and opened the destination.
- Started practice with 3 allocated items. First item `q_lean_keys_composite_null_rule@1`.
- `q_lean_keys_composite_null_rule@1`, hard, option 2 (correct). Score 0.756 → 0.805, supported confidence. No misconception signal. Recommendation `PRACTICE_HARD` for `relational.keys`, Try an available hard question to build evidence for this topic.
- `q_lean_keys_composite_unique_scope@1`, hard, option 1 (correct). Score 0.805 → 0.844, supported confidence. No misconception signal. Recommendation `LEARN` for `er.entities`, Your independent work supports moving on to Entities and attributes.
- Followed `/learn/lesson_intro_er_entities@1?difficulty=easy&fresh=1` and opened the destination.
- Progress showed 10 attempts, 10 independent responses and supported confidence.

### unrelated

- Started practice with 5 allocated items. First item `q_keys_detector_members@1`.
- `q_keys_detector_members@1`, easy, option 0 (incorrect). Score 0.500 → 0.400, insufficient confidence. No misconception signal. Recommendation `RETEACH` for `relational.keys`, Your recent answers suggest reviewing the concept before more practice.
- `q_lean_keys_candidate_count@1`, easy, option 2 (incorrect). Score 0.400 → 0.320, insufficient confidence. No misconception signal. Recommendation `RETEACH` for `relational.keys`, Your recent answers suggest reviewing the concept before more practice.
- `q_lean_keys_composite@1`, easy, option 1 (incorrect). Score 0.320 → 0.256, emerging confidence. No misconception signal. Recommendation `RETEACH` for `relational.keys`, Your recent answers suggest reviewing the concept before more practice.
- `q_lean_keys_fk_target@1`, easy, option 2 (incorrect). Score 0.256 → 0.205, emerging confidence. No misconception signal. Recommendation `RETEACH` for `relational.keys`, Your recent answers suggest reviewing the concept before more practice.
- `q_lean_keys_migrate_children@1`, easy, option 2 (incorrect). Score 0.205 → 0.164, emerging confidence. No misconception signal. Recommendation `RETEACH` for `relational.keys`, Your recent answers suggest reviewing the concept before more practice.
- Started practice with 5 allocated items. First item `q_practice_keys_missing@1`.
- `q_practice_keys_missing@1`, easy, option 1 (correct). Score 0.164 → 0.331, supported confidence. No misconception signal. Recommendation `LEARN` for `er.entities`, Fresh practice at a suitable level is unavailable here. Continue with Entities and attributes while this topic remains open for review.
- `q_keys_detector_members@1`, easy, option 3 (incorrect). Score 0.331 → 0.331, supported confidence. No misconception signal. Recommendation `RETEACH` for `relational.keys`, Your recent answers suggest reviewing the concept before more practice.
- Progress showed 7 attempts, 6 independent responses and supported confidence.

### exhaustion

- Started practice with 3 allocated items. First item `q_lean_select_null_filter@1`.
- `q_lean_select_null_filter@1`, easy, option 2 (correct). Score 0.500 → 0.600, insufficient confidence. No misconception signal. Recommendation `SQL_PRACTICE` for `sql.null`, Apply this concept to an unattempted SQL exercise.
- `q_progress_null_or_unknown@1`, medium, option 2 (correct). Score 0.600 → 0.680, insufficient confidence. No misconception signal. Recommendation `SQL_PRACTICE` for `sql.null`, Apply this concept to an unattempted SQL exercise.
- `q_progress_null_zero_or_missing@1`, easy, option 2 (correct). Score 0.680 → 0.744, emerging confidence. No misconception signal. Recommendation `SQL_PRACTICE` for `sql.null`, Apply this concept to an unattempted SQL exercise.
- Followed `/sql?exercise=sql_unassigned_orders` and opened the destination.
- Progress showed 3 attempts, 3 independent responses and emerging confidence.

## Regression and verdict

The 30 new items passed separate-context AI verification and both S1 and S4 learner content gates. The full backend run passed 164 tests with Ruff and mypy. Frontend lint, TypeScript, production build and two Vitest tests passed. Six signed-in Chrome journeys passed against the actual reviewed bank in temporary databases. Four baseline Chrome scenarios and the authored demo regression were also executed. The existing A/B CLI replay passed after publication to both local databases.

**PASS for the requested local learning journeys**, with the coverage limitations above. The measured results demonstrate application behavior for the recorded answer sequences. They do not establish educational effectiveness in a human study.
