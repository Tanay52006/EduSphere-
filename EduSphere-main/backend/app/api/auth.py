import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.analytics.wrapper import track
from app.api.dependencies import get_current_user
from app.core.db import get_db
from app.core.errors import AppError
from app.models.auth import User
from app.schemas.auth import LoginRequest, MeResponse, ProfileResponse, SignupRequest, UserResponse
from app.services.auth import authenticate, create_session, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _me(user: User) -> MeResponse:
    return MeResponse(
        user=UserResponse(id=user.id, email=user.email, created_at=user.created_at.isoformat()),
        profile=ProfileResponse.model_validate(user.profile),
    )


def set_auth_cookies(response: Response, session_token: str, app_env: str) -> None:
    secure = app_env != "development"
    response.set_cookie("edu_session", session_token, httponly=True, samesite="lax", secure=secure, max_age=1209600, path="/")
    response.set_cookie("edu_csrf", secrets.token_urlsafe(32), httponly=False, samesite="lax", secure=secure, max_age=1209600, path="/")


def _enforce_rate_limit(request: Request, email: str) -> None:
    limiter = request.app.state.rate_limiter
    ip = request.client.host if request.client else "unknown"
    allowed_ip, retry_ip = limiter.allow(f"ip:{ip}", 20)
    allowed_email, retry_email = limiter.allow(f"email:{email}", 5)
    if not allowed_ip or not allowed_email:
        retry = str(max(retry_ip, retry_email))
        raise AppError(429, "rate_limited", "Too many attempts", headers={"Retry-After": retry})


@router.post("/signup", response_model=MeResponse, status_code=201)
def signup(payload: SignupRequest, request: Request, response: Response, db: DbSession = Depends(get_db)) -> MeResponse:  # noqa: B008
    _enforce_rate_limit(request, payload.email)
    try:
        user = create_user(db, payload.email, payload.password)
    except IntegrityError as exc:
        raise AppError(409, "account_unavailable", "Unable to create account") from exc
    _, raw_token = create_session(db, user, request.headers.get("user-agent"))
    set_auth_cookies(response, raw_token, request.app.state.settings.app_env)
    track("Signed Up", {"user_id": user.id})
    return _me(user)


@router.post("/login", response_model=MeResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: DbSession = Depends(get_db)) -> MeResponse:  # noqa: B008
    _enforce_rate_limit(request, payload.email)
    user = authenticate(db, payload.email, payload.password)
    if user is None:
        raise AppError(401, "invalid_credentials", "Invalid email or password")
    _, raw_token = create_session(db, user, request.headers.get("user-agent"))
    set_auth_cookies(response, raw_token, request.app.state.settings.app_env)
    track("Logged In", {"user_id": user.id})
    return _me(user)


@router.post("/logout", status_code=204, dependencies=[Depends(get_current_user)])
def logout(request: Request, response: Response, db: DbSession = Depends(get_db)) -> Response:  # noqa: B008
    session = request.state.session
    session.revoked_at = datetime.now(UTC)
    db.commit()
    secure = request.app.state.settings.app_env != "development"
    response.delete_cookie("edu_session", path="/", secure=secure, httponly=True, samesite="lax")
    response.delete_cookie("edu_csrf", path="/", secure=secure, httponly=False, samesite="lax")
    response.status_code = 204
    return response


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> MeResponse:  # noqa: B008
    return _me(user)
