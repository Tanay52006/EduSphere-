import re
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, func, literal, select
from sqlalchemy.orm import Session

from app.ai.activities import generate_activity
from app.analytics import wrapper as analytics
from app.api.dependencies import get_current_user
from app.api.questions import owned_document
from app.core.db import get_db
from app.core.errors import AppError
from app.models.auth import User
from app.models.learning import GenerationRun, LearningActivity
from app.models.library import Chunk
from app.schemas.activities import GenerateActivity, RunActivity, StartActivity
from app.services.activities import activity_card, activity_session, score_activity, session_view, start_activity
from app.services.activity_catalog import CATALOG, authored
from app.services.games import lock_user, open_session
from app.services.progress import award_game, summary

router = APIRouter(prefix="/activities", tags=["learning-activities"])


@router.get("")
def catalog(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    cards = [activity_card(key, authored(key)) for key in CATALOG]  # type: ignore[arg-type]
    rows = db.scalars(select(LearningActivity).where(LearningActivity.user_id == user.id).order_by(LearningActivity.created_at.desc())).all()
    cards.extend(activity_card(row.id, row.content, row.document_id) for row in rows)
    settings = request.app.state.settings
    return {"activities": cards, "preview_mode": settings.llm_provider == "mock" and not settings.gemini_use_vertex}


@router.post("/generate", status_code=201)
async def generate(payload: GenerateActivity, request: Request, user: User = Depends(get_current_user),  # noqa: B008
                   db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    document = owned_document(db, user.id, payload.document_id)
    if document.status != "ready":
        raise AppError(409, "document_not_ready", "Wait for your material to finish processing.")
    lock_user(db, user)
    count = db.scalar(select(func.count()).select_from(GenerationRun).where(GenerationRun.user_id == user.id,
                       GenerationRun.created_at >= datetime.now(UTC) - timedelta(days=1))) or 0
    if count >= 5:
        raise AppError(429, "generation_limit", "You have used 5 generations in the past 24 hours. Try again later.")
    stored = db.scalar(select(func.count()).select_from(LearningActivity).where(LearningActivity.user_id == user.id,
                       LearningActivity.document_id == document.id)) or 0
    if stored >= 12:
        raise AppError(409, "activity_limit", "This document already has 12 games. Play an existing one.")
    query = select(Chunk).where(Chunk.user_id == user.id, Chunk.document_id == document.id)
    terms = list(dict.fromkeys(re.findall(r"\w{3,}", payload.focus.lower())))[:8]
    if terms:
        relevance = sum((case((func.lower(Chunk.text).contains(term, autoescape=True), 1), else_=0) for term in terms), literal(0))
        query = query.order_by(relevance.desc())
    chunks = db.scalars(query.order_by(Chunk.ordinal).limit(8)).all()
    if not chunks:
        raise AppError(409, "no_text", "This material has no readable text yet.")
    run = GenerationRun(user_id=user.id, document_id=document.id, purpose="activity")
    db.add(run)
    db.commit()
    run_id = run.id
    try:
        blueprint = await generate_activity(request.app.state.llm_provider, chunks, payload.focus)
        owned_document(db, user.id, payload.document_id)
        lock_user(db, user)
        stored = db.scalar(select(func.count()).select_from(LearningActivity).where(LearningActivity.user_id == user.id,
                           LearningActivity.document_id == payload.document_id)) or 0
        if stored >= 12:
            raise AppError(409, "activity_limit", "This document already has 12 games. Play an existing one.")
        used = {item.source_chunk_id for item in blueprint.items}
        sources = [{"title": f"{document.original_filename} · p. {c.page_start}",
                    "url": f"/api/documents/{document.id}/file#page={c.page_start}"} for c in chunks if c.id in used]
        activity = LearningActivity(user_id=user.id, document_id=document.id, content={"blueprint": blueprint.model_dump(mode="json"),
                                    "sources": sources, "preview": request.app.state.settings.llm_provider == "mock"
                                    and not request.app.state.settings.gemini_use_vertex})
        db.add(activity)
        run.status, run.generated, run.accepted = "completed", 1, 1
        db.commit()
    except Exception:
        db.rollback()
        remaining = db.get(GenerationRun, run_id)
        if remaining:
            remaining.status = "failed"
            db.commit()
        raise
    analytics.track("Learning Game Generated", {"mechanic": blueprint.mechanic, "cards": len(blueprint.items)})
    return activity_card(activity.id, activity.content, activity.document_id)


@router.post("/start", status_code=201)
def start(payload: StartActivity, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    game = start_activity(db, user, payload.activity_id)
    db.commit()
    return session_view(game)


@router.get("/sessions/{session_id}")
def resume(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    return session_view(activity_session(db, user, session_id))


@router.post("/sessions/{session_id}/run")
def run(session_id: str, payload: RunActivity, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    game = activity_session(db, user, session_id)
    if game.status == "completed":
        return session_view(game)
    open_session(game, "activity")
    feedback = score_activity(game, payload)
    game.state = {**game.state, "draft": payload.model_dump(mode="json"), "moves": game.state["moves"] + 1, "feedback": feedback}
    if feedback["correct"]:
        game.state = {**game.state, "correct": 1, "score": 100}
        xp = award_game(db, user, game, 1.0)
        game.status = "completed"
        db.flush()
        game.result = {"xp_earned": xp, "progress": summary(db, user), "explanation": feedback["message"]}
        analytics.track("Game Completed", {"game": "activity", "mechanic": game.state["content"]["blueprint"]["mechanic"], "xp_earned": xp})
    db.commit()
    return session_view(game)
