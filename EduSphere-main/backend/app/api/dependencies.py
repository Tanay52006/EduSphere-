from fastapi import Depends, Request
from sqlalchemy.orm import Session as DbSession

from app.core.db import get_db
from app.core.errors import AppError
from app.models.auth import User
from app.services.auth import find_session


def get_current_user(request: Request, db: DbSession = Depends(get_db)) -> User:  # noqa: B008
    raw_token = request.cookies.get("edu_session")
    session = find_session(db, raw_token) if raw_token else None
    if session is None:
        raise AppError(401, "unauthenticated", "Authentication required")
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        csrf_cookie = request.cookies.get("edu_csrf")
        csrf_header = request.headers.get("X-CSRF-Token")
        if not csrf_cookie or csrf_header != csrf_cookie:
            raise AppError(403, "csrf_failed", "CSRF validation failed")
    user = db.get(User, session.user_id)
    if user is None:
        raise AppError(401, "unauthenticated", "Authentication required")
    request.state.session = session
    return user
