import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.ai.questions import generate_questions
from app.analytics import wrapper as analytics
from app.api.dependencies import get_current_user
from app.core.db import get_db
from app.core.errors import AppError
from app.models.auth import User
from app.models.learning import GenerationRun, Question
from app.models.library import Chunk, Document
from app.schemas.learning import QuestionEdit

router = APIRouter(tags=["questions"])


def owned_document(db: Session, user_id: str, document_id: str) -> Document:
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user_id))
    if document is None:
        raise AppError(404, "not_found", "Resource not found")
    return document


def owned_question(db: Session, user_id: str, question_id: str) -> Question:
    question = db.scalar(select(Question).where(Question.id == question_id, Question.user_id == user_id, Question.deleted.is_(False)))
    if question is None:
        raise AppError(404, "not_found", "Resource not found")
    return question


def question_view(question: Question) -> dict[str, Any]:
    return {"id": question.id, "kind": question.kind, "prompt": question.prompt, **question.content,
            "validated": question.validated, "flagged": question.flagged}


@router.get("/documents/{document_id}/questions")
def question_bank(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    owned_document(db, user.id, document_id)
    rows = db.scalars(select(Question).where(Question.user_id == user.id, Question.document_id == document_id, Question.deleted.is_(False))).all()
    latest = db.scalar(select(GenerationRun).where(GenerationRun.user_id == user.id, GenerationRun.document_id == document_id,
                                                  GenerationRun.purpose == "questions", GenerationRun.status == "completed")
                       .order_by(GenerationRun.created_at.desc()))
    return {"questions": [question_view(q) for q in rows], "quality": {"generated": latest.generated, "accepted": latest.accepted,
            "pass_rate": latest.accepted / latest.generated} if latest and latest.generated else None}


@router.post("/documents/{document_id}/questions/generate", status_code=201)
async def generate(document_id: str, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    document = owned_document(db, user.id, document_id)
    if document.status != "ready":
        raise AppError(409, "document_not_ready", "Wait for this PDF to finish processing, then try again.")
    db.execute(update(User).where(User.id == user.id).values(id=user.id))
    count = db.scalar(select(func.count()).select_from(GenerationRun).where(GenerationRun.user_id == user.id,
                       GenerationRun.created_at >= datetime.now(UTC) - timedelta(days=1))) or 0
    if count >= 5:
        raise AppError(429, "generation_limit", "You have used 5 generations in the past 24 hours. Try again later.")
    existing = db.scalar(select(func.count()).select_from(Question).where(Question.user_id == user.id, Question.document_id == document_id,
                                                                         Question.deleted.is_(False))) or 0
    if existing >= 100:
        raise AppError(409, "bank_full", "This bank has 100 questions. Remove some before generating more.")
    chunks = db.scalars(select(Chunk).where(Chunk.document_id == document_id, Chunk.user_id == user.id).order_by(Chunk.ordinal).limit(8)).all()
    if not chunks:
        raise AppError(409, "no_text", "This PDF has no readable text yet.")
    run = GenerationRun(user_id=user.id, document_id=document_id)
    db.add(run)
    db.commit()
    run_id = run.id
    try:
        accepted, generated = await generate_questions(request.app.state.llm_provider, chunks)
        # Recheck ownership after the provider call: a deleted PDF must not be resurrected.
        owned_document(db, user.id, document_id)
        db.execute(update(User).where(User.id == user.id).values(id=user.id))
        existing = db.scalar(select(func.count()).select_from(Question).where(Question.user_id == user.id, Question.document_id == document_id,
                                                                             Question.deleted.is_(False))) or 0
        existing_prompts = set(db.scalars(select(Question.prompt).where(Question.user_id == user.id, Question.document_id == document_id,
                                                                       Question.deleted.is_(False))))
        added = 0
        for draft in accepted:
            if draft.prompt in existing_prompts or existing + added >= 100:
                continue
            chunk = next(c for c in chunks if c.id == draft.source_chunk_id)
            content = draft.model_dump(exclude={"kind", "prompt"})
            content["sources"] = [{"chunk_id": chunk.id, "page_start": chunk.page_start, "page_end": chunk.page_end,
                                   "url": f"/api/documents/{document_id}/file#page={chunk.page_start}"}]
            db.add(Question(user_id=user.id, document_id=document_id, kind=draft.kind, prompt=draft.prompt, content=content))
            existing_prompts.add(draft.prompt)
            added += 1
        run.status, run.generated, run.accepted = "completed", generated, len(accepted)
        db.commit()
    except Exception:
        db.rollback()
        remaining = db.get(GenerationRun, run_id)
        if remaining:
            remaining.status = "failed"
            db.commit()
        raise
    analytics.track("Games Generated", {"document_id": hashlib.sha256(document_id.encode()).hexdigest(),
                                      "validated_pct": round(100 * len(accepted) / generated), "game_count": 2})
    return {"generated": generated, "accepted": len(accepted), "added": added, "pass_rate": len(accepted) / generated}


@router.patch("/questions/{question_id}")
def edit(question_id: str, payload: QuestionEdit, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    question = owned_question(db, user.id, question_id)
    question.prompt, question.validated = payload.prompt, False
    db.commit()
    return question_view(question)


@router.post("/questions/{question_id}/flag", status_code=204)
def flag(question_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:  # noqa: B008
    question = owned_question(db, user.id, question_id)
    question.flagged = True
    db.commit()
    return Response(status_code=204)


@router.delete("/questions/{question_id}", status_code=204)
def delete(question_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:  # noqa: B008
    question = owned_question(db, user.id, question_id)
    question.deleted = True
    db.commit()
    return Response(status_code=204)


@router.get("/documents/{document_id}/file")
def source_file(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> FileResponse:  # noqa: B008
    from pathlib import Path

    document = owned_document(db, user.id, document_id)
    if not Path(document.storage_key).is_file():
        raise AppError(404, "not_found", "Source PDF is unavailable")
    return FileResponse(document.storage_key, media_type="application/pdf", filename=document.original_filename, content_disposition_type="inline")
