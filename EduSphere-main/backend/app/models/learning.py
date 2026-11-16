from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(12))
    prompt: Mapped[str] = mapped_column(Text)
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    validated: Mapped[bool] = mapped_column(default=True)
    flagged: Mapped[bool] = mapped_column(default=False)
    deleted: Mapped[bool] = mapped_column(default=False)


class GenerationRun(Base):
    __tablename__ = "question_generation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(16), default="running")
    purpose: Mapped[str] = mapped_column(String(16), default="questions", server_default="questions")
    generated: Mapped[int] = mapped_column(Integer, default=0)
    accepted: Mapped[int] = mapped_column(Integer, default=0)


class LearningActivity(Base):
    __tablename__ = "learning_activities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GameSession(Base):
    __tablename__ = "game_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=True)
    game: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(16), default="open")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    state: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class XPEvent(Base):
    __tablename__ = "xp_events"
    __table_args__ = (UniqueConstraint("user_id", "source", "ref"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(32))
    ref: Mapped[str] = mapped_column(String(64))
    amount: Mapped[int] = mapped_column(Integer)
    local_day: Mapped[str] = mapped_column(String(10), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Streak(Base):
    __tablename__ = "streaks"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    last_day: Mapped[str | None] = mapped_column(String(10), nullable=True)
    current: Mapped[int] = mapped_column(Integer, default=0)
    longest: Mapped[int] = mapped_column(Integer, default=0)
    freeze_week: Mapped[str | None] = mapped_column(String(10), nullable=True)


class UserBadge(Base):
    __tablename__ = "user_badges"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
