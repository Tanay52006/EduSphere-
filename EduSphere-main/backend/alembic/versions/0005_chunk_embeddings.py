"""Add persistent local embedding rows."""

import sqlalchemy as sa

from alembic import op

revision = "0005_chunk_embeddings"
down_revision = "0004_chunk_search"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chunk_embeddings",
        sa.Column("chunk_id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("document_id", sa.String(36), nullable=False),
        sa.Column("vector_json", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_chunk_embeddings_user_document", "chunk_embeddings", ["user_id", "document_id"])


def downgrade() -> None:
    op.drop_index("ix_chunk_embeddings_user_document", table_name="chunk_embeddings")
    op.drop_table("chunk_embeddings")
