"""Create user-scoped validated question bank."""

import sqlalchemy as sa

from alembic import op

revision = "0006_questions"
down_revision = "0005_chunk_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The parallel learning-games branch may already own the canonical table.
    if sa.inspect(op.get_bind()).has_table("questions"):
        return
    op.create_table(
        "questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(24), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("answer_json", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(24), nullable=False),
        sa.Column("topic", sa.String(160), nullable=False),
        sa.Column("source_chunk_ids_json", sa.Text(), nullable=False),
        sa.Column("validated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_questions_user_id", "questions", ["user_id"])
    op.create_index("ix_questions_document_id", "questions", ["document_id"])
    op.create_index("ix_questions_validated", "questions", ["validated"])
    op.create_index("ix_questions_user_document", "questions", ["user_id", "document_id"])
    op.create_index("ix_questions_user_validated", "questions", ["user_id", "validated"])


def downgrade() -> None:
    op.drop_table("questions")
