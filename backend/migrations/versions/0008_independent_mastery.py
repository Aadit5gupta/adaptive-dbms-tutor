"""Rebuild current mastery from independent answers while preserving history."""

from alembic import op

revision = "0008_independent_mastery"
down_revision = "0007_ai_review"
branch_labels = None
depends_on = None


def rebuild(*, legacy: bool) -> None:
    # Both formulas replay the append order within a topic. The old model
    # counted retries in the score and used first unhinted attempts for confidence.
    evidence_order = "hint_used, sequence" if legacy else "sequence"
    eligible = "1" if legacy else "independent"
    op.execute(f"""
        WITH RECURSIVE attempts_by_topic AS (
            SELECT a.user_id, q.subtopic_id, v.question_id, a.correct, a.hint_used,
                   a.rowid AS sequence
            FROM attempts a
            JOIN question_versions v ON v.id = a.question_version_id
            JOIN questions q ON q.id = v.question_id
            WHERE a.context NOT IN ('pre_test_a', 'post_test_b')
        ),
        marked AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY user_id, subtopic_id ORDER BY sequence
                   ) AS position,
                   hint_used = 0 AND ROW_NUMBER() OVER (
                       PARTITION BY user_id, question_id ORDER BY {evidence_order}
                   ) = 1 AS independent
            FROM attempts_by_topic
        ),
        projection(user_id, subtopic_id, position, score, distinct_count) AS (
            SELECT DISTINCT user_id, subtopic_id, 0, 0.5, 0 FROM marked
            UNION ALL
            SELECT p.user_id, p.subtopic_id, m.position,
                   CASE WHEN {eligible} THEN ROUND(p.score + 0.2 * (m.correct - p.score), 12)
                        ELSE p.score END,
                   p.distinct_count + m.independent
            FROM projection p JOIN marked m
              ON m.user_id = p.user_id AND m.subtopic_id = p.subtopic_id AND m.position = p.position + 1
        ),
        final AS (
            SELECT p.* FROM projection p WHERE NOT EXISTS (
                SELECT 1 FROM marked m
                WHERE m.user_id = p.user_id AND m.subtopic_id = p.subtopic_id
                    AND m.position = p.position + 1
            )
        )
        UPDATE mastery
        SET score = final.score,
            distinct_question_count = final.distinct_count,
            confidence_level = CASE WHEN final.distinct_count >= 6 THEN 'supported'
                                    WHEN final.distinct_count >= 3 THEN 'emerging'
                                    ELSE 'insufficient' END
        FROM final
        WHERE mastery.user_id = final.user_id AND mastery.subtopic_id = final.subtopic_id
            AND mastery.model_name = 'bounded_evidence'
    """)


def upgrade() -> None:
    rebuild(legacy=False)


def downgrade() -> None:
    rebuild(legacy=True)
