from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    goal: Mapped[str | None] = mapped_column(String(280), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    locale: Mapped[str] = mapped_column(String(10), default="en")
    path_preference: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notification_consent: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=lambda: {"push": False, "email": False, "in_app": False}
    )
    onboarding_completed: Mapped[bool] = mapped_column(default=False)
    user: Mapped[User] = relationship(back_populates="profile")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True)
    user: Mapped[User] = relationship(back_populates="sessions")
