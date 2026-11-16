from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.db import Base
from app.models.auth import Profile, User
from app.models.learning import GameSession, Streak, XPEvent
from app.models.library import Document
from app.services.progress import award_game, level_for, local_today, summary


def test_level_boundaries_and_local_midnight() -> None:
    assert level_for(0) == (1, 0, 150)
    assert level_for(149) == (1, 149, 150)
    assert level_for(150) == (2, 0, 200)
    assert level_for(350) == (3, 0, 250)
    user = User(email="test@example.com", password_hash="test", profile=Profile(timezone="Asia/Kolkata"))
    assert local_today(user, datetime(2026, 11, 12, 19, 0, tzinfo=UTC)) == date(2026, 11, 13)
    user.profile.timezone = "America/New_York"
    assert local_today(user, datetime(2026, 11, 12, 1, 0, tzinfo=UTC)) == date(2026, 11, 11)
    assert ZoneInfo("America/New_York") is not None


def test_game_cap_daily_bonus_replay_decay_and_weekly_freeze(tmp_path: Any, monkeypatch: Any) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'xp.db'}")
    Base.metadata.create_all(engine)
    today = date(2026, 11, 12)
    monkeypatch.setattr("app.services.progress.local_today", lambda user: today)
    with Session(engine) as db:
        user = User(email="test@example.com", password_hash="test", profile=Profile(timezone="UTC"))
        db.add(user)
        db.flush()
        doc = Document(user_id=user.id, original_filename="test.pdf", storage_key="test", content_hash="a" * 64,
                       mime_type="application/pdf", size_bytes=1, status="ready")
        db.add(doc)
        db.flush()
        db.add(Streak(user_id=user.id, last_day=str(today - timedelta(days=2)), current=4, longest=4))
        db.flush()
        for i in range(10):
            game = GameSession(user_id=user.id, document_id=doc.id, game="quiz_blitz", status="finished",
                               started_at=datetime.now(UTC), state={"fingerprint": str(i)})
            db.add(game)
            db.flush()
            amount = award_game(db, user, game, 1.0)
            assert amount == (75 if i == 0 else 50 if i < 4 else 0)
            game.status = "completed"
            db.flush()
        assert summary(db, user)["total_xp"] == 225
        assert db.scalar(select(func.count()).select_from(XPEvent).where(XPEvent.source == "daily_goal")) == 1
        assert db.get(Streak, user.id).current == 5
        assert db.get(Streak, user.id).freeze_week == "2026-46"

        today += timedelta(days=2)
        game = GameSession(user_id=user.id, document_id=doc.id, game="quiz_blitz", status="finished",
                           started_at=datetime.now(UTC), state={"fingerprint": "0"})
        db.add(game)
        db.flush()
        assert award_game(db, user, game, 1.0) == 50  # 25 replay XP + first activity + goal.
        assert db.get(Streak, user.id).current == 1  # This week's freeze was already used.
