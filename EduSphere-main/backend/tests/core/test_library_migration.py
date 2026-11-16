from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command

BACKEND = Path(__file__).resolve().parents[2]


def test_fresh_database_has_user_scoped_library_and_job_tables(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'library.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        config = Config(str(BACKEND / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND / "alembic"))
        command.upgrade(config, "head")
    finally:
        get_settings.cache_clear()

    inspector = inspect(create_engine(db_url))
    assert {
        "documents",
        "chunks",
        "topics",
        "jobs",
        "questions",
        "xp_events",
        "streaks",
        "user_badges",
        "game_sessions",
        "question_generation_runs",
        "learning_activities",
        "chunk_search",
        "chunk_embeddings",
    } <= set(inspector.get_table_names())
    for table in ("documents", "chunks", "topics", "jobs"):
        assert "user_id" in {column["name"] for column in inspector.get_columns(table)}
    assert {"document_id", "kind", "prompt", "content", "validated", "flagged", "deleted"} <= {
        column["name"] for column in inspector.get_columns("questions")
    }
    for table in ("xp_events", "streaks", "user_badges", "game_sessions"):
        assert "user_id" in {column["name"] for column in inspector.get_columns(table)}


def test_fts_migration_backfills_existing_chunks(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'backfill.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        config = Config(str(BACKEND / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND / "alembic"))
        command.upgrade(config, "0003_library_and_rag")
        engine = create_engine(db_url)
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO users (id, email, password_hash) VALUES ('u1', 'u1@example.com', 'hash')"))
            connection.execute(
                text(
                    "INSERT INTO documents (id, user_id, original_filename, storage_key, content_hash, mime_type, size_bytes) "
                    "VALUES ('d1', 'u1', 'notes.pdf', 'key', 'hash', 'application/pdf', 1)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO chunks (id, user_id, document_id, ordinal, text, page_start, page_end, token_count) "
                    "VALUES ('c1', 'u1', 'd1', 0, 'binary search', 1, 1, 2)"
                )
            )
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT chunk_id FROM chunk_search WHERE user_id = 'u1' AND chunk_search MATCH 'binary'")).scalar_one() == "c1"
        engine.dispose()
    finally:
        get_settings.cache_clear()
