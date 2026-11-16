import logging
import re
import uuid
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.ai.factory import create_provider
from app.api.activities import router as activities_router
from app.api.auth import router as auth_router
from app.api.chain import router as chain_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.games import router as games_router
from app.api.health import router as health_router
from app.api.onboarding import router as onboarding_router
from app.api.profile import router as profile_router
from app.api.questions import router as questions_router
from app.api.search import router as search_router
from app.core.config import Settings, get_settings
from app.core.db import Base
from app.core.errors import AppError
from app.repos.file_store import LocalFileStore
from app.services.ingestion import MAX_DOCUMENT_BYTES
from app.services.rate_limit import InMemoryRateLimiter

logger = logging.getLogger("edusphere.request")
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        supplied = request.headers.get("x-request-id", "")
        request_id = supplied if _REQUEST_ID_RE.fullmatch(supplied) else str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "no-referrer"
        response.headers["permissions-policy"] = "camera=(), microphone=(), geolocation=()"
        logger.info("request_id=%s method=%s path=%s status=%s", request_id, request.method, request.url.path, response.status_code)
        return response


def _error(request: Request, code: str, message: str) -> dict[str, object]:
    return {"error": {"code": code, "message": message}, "request_id": request.state.request_id}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="EduSphere API", version=settings.app_version)
    app.state.settings = settings
    if settings.database_url.startswith("sqlite"):
        Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
    app.state.session_local = sessionmaker(bind=engine, expire_on_commit=False)
    app.state.file_store = LocalFileStore(settings.storage_dir, max_size=MAX_DOCUMENT_BYTES)
    app.state.rate_limiter = InMemoryRateLimiter()
    app.state.llm_provider = create_provider(settings)
    if settings.auto_create_tables:
        Base.metadata.create_all(engine)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = "Resource not found" if exc.status_code == 404 else "Request failed"
        return JSONResponse(status_code=exc.status_code, content=_error(request, code, message))

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        response = JSONResponse(status_code=exc.status_code, content=_error(request, exc.code, exc.message))
        response.headers.update(exc.headers)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        del exc
        return JSONResponse(status_code=422, content=_error(request, "validation_error", "Invalid request"))

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error request_id=%s type=%s", request.state.request_id, type(exc).__name__)
        return JSONResponse(status_code=500, content=_error(request, "internal_error", "Internal server error"))

    app.include_router(health_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(profile_router, prefix="/api")
    app.include_router(onboarding_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")
    app.include_router(search_router, prefix="/api")
    app.include_router(questions_router, prefix="/api")
    app.include_router(games_router, prefix="/api")
    app.include_router(chain_router, prefix="/api")
    app.include_router(activities_router, prefix="/api")
    return app


app = create_app()
