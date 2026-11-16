from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics import wrapper as analytics
from app.models.auth import User
from app.models.learning import GameSession, Streak, UserBadge, XPEvent

BADGES = {"first_game": ("First session", 1), "perfect_quiz": ("Perfect recall", 1),
          "streak_3": ("Finding a rhythm", 3), "streak_7": ("A week of curiosity", 7)}


def local_today(user: User, now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(ZoneInfo(user.profile.timezone)).date()


def level_for(xp: int) -> tuple[int, int, int]:
    level = 1
    while xp >= 100 + 50 * level:
        xp -= 100 + 50 * level
        level += 1
    return level, xp, 100 + 50 * level


def summary(db: Session, user: User) -> dict[str, Any]:
    today = local_today(user)
    total = int(db.scalar(select(func.coalesce(func.sum(XPEvent.amount), 0)).where(XPEvent.user_id == user.id)) or 0)
    daily = int(db.scalar(select(func.coalesce(func.sum(XPEvent.amount), 0)).where(XPEvent.user_id == user.id, XPEvent.local_day == str(today))) or 0)
    activities = int(db.scalar(select(func.count()).select_from(GameSession).where(GameSession.user_id == user.id, GameSession.status == "completed")) or 0)
    streak = db.get(Streak, user.id)
    current = streak.current if streak and streak.last_day and (today - date.fromisoformat(streak.last_day)).days <= 1 else 0
    level, into, needed = level_for(total)
    earned = {b.key for b in db.scalars(select(UserBadge).where(UserBadge.user_id == user.id))}
    return {"total_xp": total, "today_xp": daily, "level": level, "level_xp": into, "level_target": needed,
            "tier": ["Curious", "Explorer", "Scholar", "Sage"][min((level - 1) // 5, 3)],
            "streak": current, "longest_streak": streak.longest if streak else 0, "daily_goal": 20,
            "daily_goal_met": daily >= 20, "activities": activities,
            "badges": [{"key": key, "name": title, "earned": key in earned} for key, (title, _) in BADGES.items()]}


def award_game(db: Session, user: User, game: GameSession, accuracy: float) -> int:
    today = local_today(user)
    day = str(today)
    old_level = summary(db, user)["level"]
    prior = db.scalars(select(GameSession).where(GameSession.user_id == user.id, GameSession.document_id == game.document_id,
                                               GameSession.game == game.game, GameSession.status == "completed")).all()
    replay_count = sum(s.state["fingerprint"] == game.state["fingerprint"] for s in prior)
    used = int(db.scalar(select(func.coalesce(func.sum(XPEvent.amount), 0)).where(XPEvent.user_id == user.id,
                      XPEvent.source == "game", XPEvent.local_day == day)) or 0)
    base = 25 if game.game in {"chain_reaction", "activity"} else 10 + round(40 * accuracy)
    amount = min(max(0, 200 - used), base // (replay_count + 1))

    def add(source: str, ref: str, xp: int) -> None:
        db.add(XPEvent(user_id=user.id, source=source, ref=ref, amount=xp, local_day=day))

    add("game", game.id, amount)
    first = db.scalar(select(XPEvent.id).where(XPEvent.user_id == user.id, XPEvent.source == "first_activity", XPEvent.ref == day))
    if first is None:
        add("first_activity", day, 10)
        amount += 10
        streak = db.get(Streak, user.id)
        if streak is None:
            streak = Streak(user_id=user.id, current=0, longest=0)
            db.add(streak)
        gap = (today - date.fromisoformat(streak.last_day)).days if streak.last_day else 999
        week = f"{today.isocalendar().year}-{today.isocalendar().week}"
        freeze = gap == 2 and streak.freeze_week != week
        streak.current = streak.current + 1 if gap == 1 or freeze else 1
        streak.longest = max(streak.longest, streak.current)
        streak.last_day = day
        if freeze:
            streak.freeze_week = week
            analytics.track("Streak Freeze Used", {"length": streak.current})
        analytics.track("Streak Extended", {"length": streak.current})
    db.flush()
    goal = db.scalar(select(XPEvent.id).where(XPEvent.user_id == user.id, XPEvent.source == "daily_goal", XPEvent.ref == day))
    if goal is None and summary(db, user)["today_xp"] >= 20:
        add("daily_goal", day, 15)
        amount += 15
    streak = db.get(Streak, user.id)
    keys = ["first_game"]
    if accuracy == 1 and game.game == "quiz_blitz":
        keys.append("perfect_quiz")
    for key in ("streak_3", "streak_7"):
        if streak and streak.current >= BADGES[key][1]:
            keys.append(key)
    for key in keys:
        if db.get(UserBadge, (user.id, key)) is None:
            db.add(UserBadge(user_id=user.id, key=key))
            analytics.track("Badge Earned", {"badge_key": key})
    db.flush()
    new_level = summary(db, user)["level"]
    if new_level > old_level:
        analytics.track("Level Up", {"new_level": new_level})
    analytics.track("XP Earned", {"amount": amount, "source": "game"})
    return amount
