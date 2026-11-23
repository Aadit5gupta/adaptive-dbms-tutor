"""Expose FTS-present documents for truthful library counts."""

from alembic import op

revision = "0004_source_vocabulary"
down_revision = "0003_source_passages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE VIRTUAL TABLE source_passages_fts_vocab "
        "USING fts5vocab(source_passages_fts, 'instance')"
    )


def downgrade() -> None:
    op.execute("DROP TABLE source_passages_fts_vocab")
