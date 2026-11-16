"""Add the SQLite FTS5 chunk index."""

from alembic import op

revision = "0004_chunk_search"
down_revision = "0003_library_and_rag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        op.execute(
            "CREATE VIRTUAL TABLE chunk_search USING fts5(" 
            "chunk_id UNINDEXED, user_id UNINDEXED, document_id UNINDEXED, text)"
        )
        op.execute("INSERT INTO chunk_search (chunk_id, user_id, document_id, text) SELECT id, user_id, document_id, text FROM chunks")


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        op.execute("DROP TABLE chunk_search")
