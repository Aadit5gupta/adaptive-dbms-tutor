# Educational verification and activation

Reviewed on 23 November 2026 by `ai:codex_primary` and `ai:codex_separate_context`. The second reviewer worked from a separate context and derived keys and fixture results independently. The review covered 30 MCQs, six original lessons, six SQLite exercises and three misconception definitions. All 45 passed after targeted changes. Published version references below are `@1` because these drafts had no earlier published versions.

## Chapter evidence

| Topic | Evidence used |
|---|---|
| Keys and foreign keys | Runestone §1.7 explains matching parent keys and constraint enforcement. SQLite spells out the nullable child-key case and separate uniqueness requirements on parent keys. BCcampus Ch. 7 and DataField Ch. 3 corroborate the distinction between a candidate key and a redundant superkey. [Runestone §1.7](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/07-constraints/constraints.html) · [SQLite foreign keys](https://sqlite.org/foreignkeys.html) · [BCcampus Ch. 7](https://opentextbc.ca/dbdesign01/chapter/chapter-7-the-relational-data-model/) · [DataField Ch. 3](https://datafield.dev/sql/part-01/chapter-03/) |
| Basic SELECT | Shea Ch. 2 demonstrates projection, filtering, distinct projected rows and multi-column sorting. Runestone §1.3 and SQLite cover inclusive `BETWEEN` and NULL tests. [Shea Ch. 2](https://brendanpshea.github.io/database_sql/database_ch02_select_scifi.html) · [Runestone §1.3](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/03-expressions/expressions.html) · [SQLite expressions](https://sqlite.org/lang_expr.html) · [SQLite SELECT](https://sqlite.org/lang_select.html) |
| Joins and existence | Runestone §1.4 distinguishes matching pairs from NULL-extended left rows. Shea Ch. 3 and DataField Ch. 6 corroborate the distinction. Runestone §1.8 covers correlated existence tests. [Runestone §1.4](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/04-multiple-tables/multiple-tables.html) · [Shea Ch. 3](https://brendanpshea.github.io/database_sql/database_ch03_joins_imdb.html) · [DataField Ch. 6](https://datafield.dev/sql/part-02/chapter-06/) · [Runestone §1.8](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/08-subqueries/subqueries.html) |
| Grouping | Runestone §1.9 explains grouped aggregates and `HAVING`. SQLite confirms that `COUNT(*)` counts rows and `COUNT(column)` skips NULLs. [Runestone §1.9](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/09-grouping-and-aggregation/grouping-and-aggregation.html) · [SQLite aggregate functions](https://sqlite.org/lang_aggfunc.html) |
| Keys, dependencies and normalization | Runestone §3.3.3–3.3.6 supplies minimality, functional dependency, attribute closure, second/third normal forms and decomposition. BCcampus Chapters 11 and 12 corroborate the dependency and normalization concepts. OpenStax §3.1 supports the overview of related tables and reducing redundancy through normalization. [Runestone §3.3](https://runestone.academy/ns/books/published/practical_db/PART3_RELATIONAL_DATABASE_THEORY/03-normalization/normalization.html) · [BCcampus Ch. 11](https://opentextbc.ca/dbdesign01/chapter/chapter-11-functional-dependencies/) · [BCcampus Ch. 12](https://opentextbc.ca/dbdesign01/chapter/chapter-12-normalization/) · [OpenStax §3.1](https://openstax.org/books/foundations-information-systems/pages/3-1-data-types-database-management-systems-and-tools-for-managing-data) |

## MCQ dispositions

Each row records the independently confirmed one-based key as a letter and its controlling fact. The reviewers checked each distractor against the stem's stated schema, data and query.

| Item ID | Key | Verified reasoning |
|---|:---:|---|
| `q_keys_detector_tickets` | A | Two tickets can reference existing account 9. |
| `q_keys_detector_members` | C | Repeated references to club 22 are valid. An unmatched non-NULL reference fails. |
| `q_keys_checkpoint_rooms` | B | A separate child `UNIQUE` constraint limits non-NULL room references to one booking each. |
| `q_keys_checkpoint_badges` | D | The enforced nullable child accepts NULL and another reference to office 2. |
| `q_join_detector_routes` | B | A route-side LEFT JOIN retains routes even if Departures is empty. |
| `q_join_detector_orders` | C | An INNER JOIN emits zero rows for an unmatched customer. |
| `q_join_checkpoint_households` | A | The unmatched household produces one row with NULL meter fields. |
| `q_join_checkpoint_teams` | D | Counting matched non-NULL game IDs gives Cedar two and Maple zero. |
| `q_practice_keys_missing` | B | An invoice referencing a missing account violates the enforced foreign key. |
| `q_practice_select_where` | C | The predicate retains 5 and 7. |
| `q_practice_select_columns` | A | `SELECT` emits name, then price. |
| `q_practice_count_null` | D | Two values are non-NULL. |
| `q_lean_norm_detector_registration` | B | The student part of the composite key determines the non-key student name. |
| `q_lean_norm_detector_branch` | C | Region manager follows store ID through region ID. |
| `q_lean_norm_checkpoint_order` | A | Store product name with the product and retain the order-line reference. |
| `q_lean_norm_checkpoint_depot` | D | Depot ID is the intermediate determinant. |
| `q_lean_keys_composite` | C | Branch and copy number together identify the copy. |
| `q_lean_keys_superkey` | B | The pair identifies the row and either component alone already suffices. |
| `q_lean_keys_fk_target` | A | The enforced reference needs a parent row with the same ID. |
| `q_lean_keys_candidate_count` | D | Two independent single-column identifiers are minimal. |
| `q_lean_select_between` | B | Both bounds, 9 and 10, pass the inclusive predicate. |
| `q_lean_select_null_filter` | C | `IS NULL` tests for absent tracking numbers. |
| `q_lean_select_order` | A | Use descending score and ascending student ID within ties. |
| `q_lean_select_distinct` | D | The selected column has two distinct values. |
| `q_lean_join_multiple` | B | Three matching pairs yield three rows. |
| `q_lean_join_count` | C | The unmatched group remains and its right-side IDs contribute zero. |
| `q_lean_group_filter` | A | Use `HAVING COUNT(*) >= 3` to filter aggregate groups. |
| `q_lean_group_count` | D | The group row count is three and the non-NULL value count is two. |
| `q_lean_fds_counterexample` | B | Equal route IDs with different origin cities violate the dependency. |
| `q_lean_fds_closure` | C | Beginning at A and following the given dependencies reaches A, B and C. |

Wording changes specify enforced constraint assumptions, clarify which normalization dependency is being evaluated, and make the badges checkpoint options describe the same insertion outcomes. The teams checkpoint now requires applying the outer-join concept to grouped counts. Each rule reserves its checkpoint items from diagnostic/practice allocation. An answer-revealing hint disqualifies the response as independent detector evidence.

## Original lessons and misconception rules

| Original lesson | Verified teaching example |
|---|---|
| `lesson_fk_multiplicity` | Existing non-NULL parent, repeatable child reference, and optional separate uniqueness. |
| `lesson_join_unmatched` | Branches with and without loans. Establishes that the unmatched left row stays and right columns become NULL. |
| `lesson_candidate_keys` | Minimality asks whether an attribute can be removed while retaining uniqueness. |
| `lesson_select_filter` | Prediction distinguishes selected columns and rows that satisfy the predicate. |
| `lesson_group_counts` | Counts from the same group differ when a value is NULL. |
| `lesson_dependency_chain` | Original rows illustrate the difference between depending on part of a key and depending through an intermediate determinant. |

| Rule | Independent mapped evidence | Reserved transfer checks |
|---|---|---|
| `KEYS-02` | Ticket scenario treats a child foreign key as automatically unique (B). Club scenario rejects duplicate references to the same club (D). | Badges tests acceptance of NULL and a repeat reference separately. Rooms asks the learner to choose the extra constraint. |
| `SQL-JOIN-01` | Routes chooses INNER JOIN where preservation is required (A). Orders predicts a NULL-extended row under INNER JOIN (A). | Households predicts NULL extension on the right. Teams transfers that fact to a count that must include a zero group. |
| `NORM-03` | Registration calls dependence on part of a key transitive (A). Branch calls dependence through region partial (A). | Order asks for a decomposition. Depot asks for the intermediate determinant in a different chain. |

## SQL result verification

The separate reviewer derived the expected results from each fixture and ran both query formulations through the restricted worker for all 18 exercise/fixture pairs. All 36 runs passed. Nine candidate incorrect queries diverged on at least one fixture. The regression test computes the expectations from table rows in Python and compares the stored results, reference queries and alternate queries. It also checks representative incorrect results with the worker. [SQL regression test](../backend/tests/test_educational_sql.py)

| SQL exercise | Alternate correct formulation | Important coverage |
|---|---|---|
| `sql_join_001` | Correlated count per customer | Zero orders, duplicate display names and counts greater than one. |
| `sql_sorted_customers` | Descending positional ordering | Reversed order and repeated display names. |
| `sql_matched_customers` | JOIN with DISTINCT | Several orders per customer, repeated names and no matches. |
| `sql_unassigned_orders` | Negated `IS NOT NULL` | Ordinary NULL matching, multiple NULLs and the empty-orders case. |
| `sql_customers_without_orders` | Correlated `NOT EXISTS` | Empty matches, multiple matches and NULLs in the order-side key. |
| `sql_repeat_customers` | JOIN, GROUP BY and HAVING | Multiple qualifying customers, counts above two and unassigned orders. |

The visible and first hidden fixture now contain the edge rows that distinguish common mistakes. In particular, the hidden fixture contains two qualifying customers, a count above two and two NULL customer IDs. Those rows catch hardcoded counts, a single-row limit and grouping unassigned orders as customers.
