"""Local sessions and learning preferences."""

import sqlalchemy as sa
from alembic import op

revision = "0005_accounts"
down_revision = "0004_source_vocabulary"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("token_hash", sa.String(), unique=True, nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.Column("revoked_at", sa.Integer()),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_table(
        "profiles",
        sa.Column(
            "user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("goal", sa.String()),
        sa.Column("level", sa.String()),
        sa.Column("daily_minutes", sa.Integer()),
    )


def downgrade() -> None:
    op.drop_table("profiles")
    op.drop_table("sessions")
