import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.models.auth import Profile, Session, User

password_hasher = PasswordHasher()
_DUMMY_HASH = password_hasher.hash("edusphere-dummy-password")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except Exception:
        return False


def authenticate(db: DbSession, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    password_hash = user.password_hash if user else _DUMMY_HASH
    if not verify_password(password, password_hash):
        return None
    return user


def create_user(db: DbSession, email: str, password: str) -> User:
    user = User(email=email, password_hash=password_hasher.hash(password))
    user.profile = Profile()
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def create_session(db: DbSession, user: User, user_agent: str | None) -> tuple[Session, str]:
    raw_token = secrets.token_urlsafe(32)
    session = Session(
        token_hash=hash_token(raw_token),
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=14),
        user_agent=(user_agent or "")[:256] or None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, raw_token


def find_session(db: DbSession, raw_token: str) -> Session | None:
    session = db.scalar(select(Session).where(Session.token_hash == hash_token(raw_token)))
    now = datetime.now(UTC)
    if session is None or session.revoked_at is not None:
        return None
    expires_at = session.expires_at.replace(tzinfo=UTC) if session.expires_at.tzinfo is None else session.expires_at
    if expires_at <= now:
        return None
    return session
