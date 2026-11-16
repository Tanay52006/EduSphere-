"""Question banks, game sessions and append-only XP ledger."""

import sqlalchemy as sa

from alembic import op

revision = "0006_learning_games"
down_revision = "0005_chunk_embeddings"
branch_labels = None
depends_on = None


def archive_parallel_schema() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("questions") or "type" not in {c["name"] for c in inspector.get_columns("questions")}:
        return
    names = [n for n in ("questions", "xp_events", "streaks", "badges", "user_badges", "game_sessions", "game_results") if inspector.has_table(n)]
    metadata = sa.MetaData()
    for name in names:
        original = sa.Table(name, metadata, autoload_with=bind)
        columns = []
        for column in original.columns:
            foreign_keys = []
            for fk in column.foreign_keys:
                target_table, target_column = fk.target_fullname.rsplit(".", 1)
                target = f"legacy_{target_table}" if target_table in names else target_table
                foreign_keys.append(sa.ForeignKey(f"{target}.{target_column}", ondelete=fk.ondelete))
            columns.append(sa.Column(column.name, column.type, *foreign_keys, primary_key=column.primary_key, nullable=column.nullable))
        op.create_table(f"legacy_{name}", *columns)
        archived = sa.Table(f"legacy_{name}", sa.MetaData(), autoload_with=bind)
        bind.execute(archived.insert().from_select(list(original.columns.keys()), sa.select(original)))
    for name in reversed(names):
        op.drop_table(name)


def upgrade() -> None:
    archive_parallel_schema()
    op.create_table(
        "questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(12), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("validated", sa.Boolean(), nullable=False),
        sa.Column("flagged", sa.Boolean(), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "question_generation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("generated", sa.Integer(), nullable=False),
        sa.Column("accepted", sa.Integer(), nullable=False),
    )
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("game", sa.String(24), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
    )
    op.create_table(
        "xp_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("ref", sa.String(64), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("local_day", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "source", "ref"),
    )
    op.create_table(
        "streaks",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("last_day", sa.String(10)),
        sa.Column("current", sa.Integer(), nullable=False),
        sa.Column("longest", sa.Integer(), nullable=False),
        sa.Column("freeze_week", sa.String(10)),
    )
    op.create_table(
        "user_badges",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("key", sa.String(32), primary_key=True),
        sa.Column("earned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for table in ("questions", "question_generation_runs", "game_sessions", "xp_events"):
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])
    for table in ("questions", "question_generation_runs", "game_sessions"):
        op.create_index(f"ix_{table}_document_id", table, ["document_id"])
    op.create_index("ix_xp_events_local_day", "xp_events", ["local_day"])


def downgrade() -> None:
    for table in ("user_badges", "streaks", "xp_events", "game_sessions", "question_generation_runs", "questions"):
        op.drop_table(table)
