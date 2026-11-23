"""Grounded source passages and SQLite full-text index."""

import sqlalchemy as sa
from alembic import op

revision = "0003_source_passages"
down_revision = "0002_learning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_passages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("passage_key", sa.String(), nullable=False, unique=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("lesson_ref", sa.String(), sa.ForeignKey("lesson_versions.id")),
        sa.Column("book_id", sa.String()),
        sa.Column("clearance_id", sa.String()),
        sa.Column("topic_id", sa.String(), sa.ForeignKey("topics.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("license_url", sa.String()),
        sa.Column("attribution", sa.String(), nullable=False),
        sa.Column("source_hash", sa.String(), nullable=False),
        sa.CheckConstraint("kind IN ('book', 'lesson')"),
        sa.CheckConstraint(
            "(kind = 'lesson' AND lesson_ref IS NOT NULL AND book_id IS NULL AND clearance_id IS NULL)"
            " OR (kind = 'book' AND lesson_ref IS NULL AND book_id IS NOT NULL AND clearance_id IS NOT NULL)"
        ),
    )
    for column in ("lesson_ref", "book_id", "clearance_id", "topic_id"):
        op.create_index(f"ix_source_passages_{column}", "source_passages", [column])
    op.execute(
        "CREATE VIRTUAL TABLE source_passages_fts USING fts5("
        "title, body, content='source_passages', content_rowid='id', tokenize='porter unicode61')"
    )
    added = (
        "INSERT INTO source_passages_fts(rowid, title, body) VALUES (new.id, new.title, new.body);"
    )
    removed = (
        "INSERT INTO source_passages_fts(source_passages_fts, rowid, title, body) "
        "VALUES ('delete', old.id, old.title, old.body);"
    )
    for event, statements in (
        ("INSERT", added),
        ("UPDATE", removed + added),
        ("DELETE", removed),
    ):
        op.execute(
            f"CREATE TRIGGER source_passage_{event.lower()} AFTER {event} ON source_passages "
            f"BEGIN {statements} END"
        )


def downgrade() -> None:
    for event in ("insert", "update", "delete"):
        op.execute(f"DROP TRIGGER source_passage_{event}")
    op.execute("DROP TABLE source_passages_fts")
    op.drop_table("source_passages")
