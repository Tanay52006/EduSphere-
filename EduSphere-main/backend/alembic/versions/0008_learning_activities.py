"""Source-grounded reusable learning games."""
import sqlalchemy as sa

from alembic import op

revision = "0008_learning_activities"
down_revision = "0007_curated_chapters"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("question_generation_runs", sa.Column("purpose", sa.String(16), nullable=False, server_default="questions"))
    op.create_table("learning_activities",
                    sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("content", sa.JSON(), nullable=False),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_learning_activities_user_id", "learning_activities", ["user_id"])
    op.create_index("ix_learning_activities_document_id", "learning_activities", ["document_id"])


def downgrade() -> None:
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM learning_activities")).scalar():
        raise RuntimeError("Generated activities exist; retain them before downgrading.")
    op.drop_table("learning_activities")
    with op.batch_alter_table("question_generation_runs") as batch:
        batch.drop_column("purpose")
