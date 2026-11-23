"""Private tutorial conversations with account deletion cascades."""

import sqlalchemy as sa
from alembic import op

revision = "0006_tutor_threads"
down_revision = "0005_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assessment_session_items",
        sa.Column("highest_hint_level", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "tutor_conversations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("topic_id", sa.String()),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
    )
    op.create_index("ix_tutor_conversations_user_id", "tutor_conversations", ["user_id"])
    op.create_table(
        "tutor_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(),
            sa.ForeignKey("tutor_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("reply_json", sa.String()),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')"),
    )
    op.create_index("ix_tutor_messages_conversation_id", "tutor_messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_table("tutor_messages")
    op.drop_table("tutor_conversations")
    op.drop_column("assessment_session_items", "highest_hint_level")
