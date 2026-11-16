"""Create user-scoped gamification and server-authoritative game tables."""

import sqlalchemy as sa

from alembic import op

revision = "0007_gamification"
down_revision = "0006_questions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("game_sessions") and "state" in {c["name"] for c in inspector.get_columns("game_sessions")}:
        return
    op.create_table(
        "xp_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_xp_events_user_id", "xp_events", ["user_id"])
    op.create_index("ix_xp_events_user_created", "xp_events", ["user_id", "created_at"])
    op.create_table(
        "streaks",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activity_date", sa.Date()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "badges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(60), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )
    op.create_table(
        "user_badges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("badge_id", sa.String(36), sa.ForeignKey("badges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("earned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badges_user_badge"),
    )
    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])
    op.create_index("ix_user_badges_badge_id", "user_badges", ["badge_id"])
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="SET NULL")),
        sa.Column("game_type", sa.String(40), nullable=False),
        sa.Column("question_ids_json", sa.Text(), nullable=False),
        sa.Column("answer_key_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="open"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_game_sessions_user_id", "game_sessions", ["user_id"])
    op.create_index("ix_game_sessions_document_id", "game_sessions", ["document_id"])
    op.create_index("ix_game_sessions_status", "game_sessions", ["status"])
    op.create_index("ix_game_sessions_user_status", "game_sessions", ["user_id", "status"])
    op.create_table(
        "game_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("xp_earned", sa.Integer(), nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_game_results_user_id", "game_results", ["user_id"])


def downgrade() -> None:
    op.drop_table("game_results")
    op.drop_table("game_sessions")
    op.drop_table("user_badges")
    op.drop_table("badges")
    op.drop_table("streaks")
    op.drop_table("xp_events")
