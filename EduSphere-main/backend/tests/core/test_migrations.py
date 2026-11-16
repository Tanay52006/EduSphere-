from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import get_settings

BACKEND = Path(__file__).resolve().parents[2]


def test_alembic_migrates_the_configured_database(tmp_path, monkeypatch):
    """`make migrate` must target DATABASE_URL, not the URL hardcoded in alembic.ini."""
    db_url = f"sqlite:///{tmp_path / 'migrated.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()
    try:
        config = Config(str(BACKEND / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND / "alembic"))
        command.upgrade(config, "head")
    finally:
        get_settings.cache_clear()

    tables = set(inspect(create_engine(db_url)).get_table_names())
    assert {"users", "profiles", "sessions", "questions", "question_generation_runs", "game_sessions", "xp_events", "streaks", "user_badges"} <= tables
    assert "learning_activities" in tables
    columns = inspect(create_engine(db_url)).get_columns("question_generation_runs")
    assert any(column["name"] == "purpose" and not column["nullable"] for column in columns)
