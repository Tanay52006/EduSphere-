"""Allow authored chapters without a personal uploaded document."""
import sqlalchemy as sa

from alembic import op

revision = "0007_curated_chapters"
down_revision = "0006_learning_games"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("game_sessions") as batch:
        batch.alter_column("document_id", existing_type=sa.String(36), nullable=True)


def downgrade() -> None:
    # Refuse to delete authored-chapter history just to tighten the foreign key.
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM game_sessions WHERE document_id IS NULL")).scalar():
        raise RuntimeError("Authored chapter sessions exist; retain them before downgrading.")
    with op.batch_alter_table("game_sessions") as batch:
        batch.alter_column("document_id", existing_type=sa.String(36), nullable=False)
