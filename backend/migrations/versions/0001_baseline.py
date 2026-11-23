"""Baseline migration for local installations."""

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Initialize Alembic's application schema version."""


def downgrade() -> None:
    """The baseline has no application tables."""
