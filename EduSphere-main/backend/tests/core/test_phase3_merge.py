import json
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, Table, create_engine, inspect, select, text

from alembic import command
from app.core.config import get_settings

BACKEND = Path(__file__).resolve().parents[2]


def migration_config():
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    return config


def test_phase3_has_one_head_that_contains_both_histories():
    script = ScriptDirectory.from_config(migration_config())
    assert script.get_heads() == ["0009_reconcile_phase3"]
    revisions = {r.revision for r in script.walk_revisions()}
    assert {"0007_gamification", "0008_learning_activities"} <= revisions


@pytest.mark.parametrize("start", ["0005_chunk_embeddings", "0006_questions", "0007_gamification", "0008_learning_activities"])
def test_upgrade_from_either_branch_preserves_learning_data(tmp_path, monkeypatch, start):
    url = f"sqlite:///{tmp_path / 'upgrade.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    engine = create_engine(url)
    config = migration_config()
    try:
        command.upgrade(config, start)
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO users (id,email,password_hash) VALUES ('u','merge@example.test','hash')"))
            connection.execute(text("INSERT INTO documents (id,user_id,original_filename,storage_key,content_hash,mime_type,size_bytes) "
                                    "VALUES ('d','u','notes.pdf','notes.pdf','hash','application/pdf',1)"))
            connection.execute(text("INSERT INTO chunks (id,user_id,document_id,ordinal,text,page_start,page_end,token_count) "
                                    "VALUES ('c','u','d',0,'ATP is a molecule that supplies immediate energy.',1,1,9)"))
            if start in {"0006_questions", "0007_gamification"}:
                questions = Table("questions", MetaData(), autoload_with=connection)
                connection.execute(questions.insert(), {"id": "q", "user_id": "u", "document_id": "d", "type": "MCQ", "prompt": "Which molecule?",
                    "payload_json": '{"options":["ATP","DNA"]}', "answer_json": '{"value":"ATP"}', "explanation": "ATP supplies energy.",
                    "difficulty": "easy", "topic": "biology", "source_chunk_ids_json": '["c"]', "validated": True})
            if start == "0007_gamification":
                template = {"user_id": "u", "document_id": "d", "explanation": "ATP supplies energy.", "difficulty": "easy",
                            "topic": "biology", "source_chunk_ids_json": '["c"]', "validated": True}
                connection.execute(questions.insert(), {**template, "id": "tf", "type": "TF", "prompt": "ATP supplies energy.",
                                    "payload_json": '{}', "answer_json": '{"value":true}'})
                pairs = [{"id": str(i), "term": f"Term {i}", "definition": f"Definition {i}"} for i in range(6)]
                connection.execute(questions.insert(), {**template, "id": "pairs", "type": "MATCH", "prompt": "Match these concepts.",
                                    "payload_json": json.dumps({"pairs": pairs}), "answer_json": '{}'})
                connection.execute(questions.insert(), {**template, "id": "uncited", "type": "MCQ", "prompt": "Untrusted source",
                                    "payload_json": '{"options":["A","B"]}', "answer_json": '{"value":"A"}', "source_chunk_ids_json": '["other-user-chunk"]'})
                connection.execute(text("INSERT INTO badges (id,code,name,description) VALUES ('b','first_game','First game','Played a game')"))
                connection.execute(text("INSERT INTO user_badges (id,user_id,badge_id) VALUES ('ub','u','b')"))
                connection.execute(text("INSERT INTO xp_events (id,user_id,source,amount,reference) VALUES ('xp','u','game',30,'round')"))
                connection.execute(text("INSERT INTO streaks (user_id,current_streak,longest_streak,last_activity_date) VALUES ('u',2,4,'2026-11-13')"))
                connection.execute(text("INSERT INTO game_sessions (id,user_id,document_id,game_type,question_ids_json,answer_key_json,status) "
                                        "VALUES ('round','u','d','quiz_blitz','[\"q\"]','{}','open')"))
                connection.execute(text("INSERT INTO game_sessions (id,user_id,document_id,game_type,question_ids_json,answer_key_json,status) "
                                        "VALUES ('finished','u','d','quiz_blitz','[\"q\"]','{}','completed')"))
                results = Table("game_results", MetaData(), autoload_with=connection)
                connection.execute(results.insert(), {"id": "r", "user_id": "u", "session_id": "finished", "score": 100,
                    "correct_count": 1, "total_count": 1, "xp_earned": 30,
                    "answers_json": json.dumps([{"question_id": "q", "correct": True, "correct_answer": {"value": "ATP"},
                                                  "explanation": "ATP supplies energy.", "source_chunk_ids": ["c"]}])})
            if start == "0008_learning_activities":
                questions = Table("questions", MetaData(), autoload_with=connection)
                connection.execute(questions.insert(), {"id": "q", "user_id": "u", "document_id": "d", "kind": "MCQ", "prompt": "Which molecule?",
                    "content": {"answer": "ATP", "options": ["ATP", "DNA"], "sources": []}, "validated": True, "flagged": False, "deleted": False})
                connection.execute(text("INSERT INTO xp_events (id,user_id,source,ref,amount,local_day) VALUES ('xp','u','game','round',30,'2026-11-13')"))
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        inspector = inspect(engine)
        assert {"kind", "content", "flagged", "deleted"} <= {c["name"] for c in inspector.get_columns("questions")}
        assert {"learning_activities", "question_generation_runs"} <= set(inspector.get_table_names())
        with engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all() == ["0009_reconcile_phase3"]
            assert connection.execute(text("SELECT text FROM chunks WHERE id='c'")).scalar_one().startswith("ATP")
            if start != "0005_chunk_embeddings":
                active_questions = Table("questions", MetaData(), autoload_with=connection)
                q = connection.execute(select(active_questions).where(active_questions.c.id == "q")).mappings().one()
                assert q["id"] == "q" and q["user_id"] == "u" and q["validated"]
                assert q["content"]["answer"] == "ATP"
            if start in {"0007_gamification", "0008_learning_activities"}:
                assert connection.execute(text("SELECT SUM(amount) FROM xp_events WHERE user_id='u'")).scalar_one() == 30
            if start == "0007_gamification":
                assert connection.execute(text("SELECT current,longest FROM streaks WHERE user_id='u'")).one() == (2, 4)
                raw = connection.execute(text("SELECT payload_json FROM legacy_questions WHERE id='q'")).scalar_one()
                assert json.loads(raw)["options"] == ["ATP", "DNA"]
                assert connection.execute(text("SELECT status FROM legacy_game_sessions WHERE id='round'")).scalar_one() == "open"
                sessions = Table("game_sessions", MetaData(), autoload_with=connection)
                completed = connection.execute(select(sessions).where(sessions.c.id == "finished")).mappings().one()
                assert completed["status"] == "completed"
                assert completed["result"]["progress"]["total_xp"] == 30
                assert completed["result"]["review"][0]["answer"] == "ATP"
                assert completed["result"]["review"][0]["sources"][0]["chunk_id"] == "c"
                assert connection.execute(text("SELECT status FROM game_sessions WHERE id='round'")).scalar_one() == "abandoned"
                converted = connection.execute(select(active_questions).where(active_questions.c.id == "tf")).mappings().one()
                assert converted["kind"] == "MCQ" and converted["content"]["options"] == ["True", "False"]
                assert converted["content"]["answer"] == "True"
                assert connection.execute(text("SELECT COUNT(*) FROM questions WHERE kind='MATCH'")).scalar_one() == 6
                assert not connection.execute(text("SELECT validated FROM questions WHERE id='uncited'")).scalar_one()
                assert connection.execute(text("SELECT key FROM user_badges WHERE user_id='u'")).scalar_one() == "first_game"
        if start == "0007_gamification":
            with pytest.raises(RuntimeError, match="Restore a pre-upgrade backup"):
                command.downgrade(config, "0008_learning_activities")
    finally:
        engine.dispose()
        get_settings.cache_clear()
