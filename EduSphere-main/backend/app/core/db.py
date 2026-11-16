from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)


if settings.database_url.startswith("sqlite"):

    @event.listens_for(Engine, "connect")
    def _configure_sqlite(connection: object, _record: object) -> None:
        cursor = connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = getattr(request.app.state, "session_local", SessionLocal)
    with session_factory() as session:
        yield session
