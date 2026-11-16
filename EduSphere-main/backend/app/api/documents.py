from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.api.dependencies import get_current_user
from app.core.db import get_db
from app.core.errors import AppError
from app.models.auth import User
from app.models.library import Document, Job
from app.repos.keyword_store import SQLiteKeywordStore
from app.repos.vector_store import SQLiteVectorStore
from app.schemas.library import DocumentResponse
from app.services.ingestion import MAX_DOCUMENT_BYTES, IngestionError, extract_pages, validate_pdf

router = APIRouter(prefix="/documents", tags=["documents"])


def _error_for_ingestion(error: IngestionError) -> AppError:
    status_code = 413 if error.code in {"document_too_large", "user_quota_exceeded", "page_limit_exceeded"} else 400
    return AppError(status_code, error.code, "The PDF could not be accepted")


def _response(document: Document, job: Job) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        original_filename=document.original_filename,
        status=document.status,
        error_code=document.error_code or job.error_code,
        page_count=document.page_count,
        ocr_required=document.ocr_required,
        job_id=job.id,
        job_status=job.status,
        progress=job.progress,
        created_at=document.created_at,
    )


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
    db: DbSession = Depends(get_db),  # noqa: B008
) -> DocumentResponse:  # noqa: B008
    content = await file.read(MAX_DOCUMENT_BYTES + 1)
    stored_path: Path | None = None
    try:
        user_bytes = db.scalar(select(func.coalesce(func.sum(Document.size_bytes), 0)).where(Document.user_id == user.id)) or 0
        validated = validate_pdf(content, Path(file.filename or "upload.pdf").name, int(user_bytes))
        pages, ocr_required = extract_pages(validated.content)
        stored_path = request.app.state.file_store.save(file.filename or "upload.pdf", validated.content)
        document = Document(
            user_id=user.id,
            original_filename=Path(file.filename or "upload.pdf").name,
            storage_key=str(stored_path),
            content_hash=validated.content_hash,
            mime_type="application/pdf",
            size_bytes=validated.size_bytes,
            page_count=len(pages),
            status="queued",
            ocr_required=ocr_required,
        )
        db.add(document)
        db.flush()
        job = Job(user_id=user.id, document_id=document.id, job_type="document_ingestion", status="queued", progress=0)
        db.add(job)
        db.commit()
        db.refresh(document)
        db.refresh(job)
        return _response(document, job)
    except IngestionError as exc:
        if stored_path is not None:
            stored_path.unlink(missing_ok=True)
        raise _error_for_ingestion(exc) from exc
    except Exception:
        if stored_path is not None:
            stored_path.unlink(missing_ok=True)
        db.rollback()
        raise


@router.get("", response_model=list[DocumentResponse])
def list_documents(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> list[DocumentResponse]:  # noqa: B008
    documents = db.scalars(select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())).all()
    responses: list[DocumentResponse] = []
    for document in documents:
        job = db.scalar(select(Job).where(Job.document_id == document.id, Job.user_id == user.id).order_by(Job.created_at.desc()))
        if job is not None:
            responses.append(_response(document, job))
    return responses


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> Response:  # noqa: B008
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user.id))
    if document is None:
        raise AppError(404, "not_found", "Resource not found")
    keyword_store = SQLiteKeywordStore(db)
    keyword_store.ensure_schema()
    keyword_store.delete_by_document(user.id, document.id)
    SQLiteVectorStore(db).delete_by_document(user.id, document.id)
    Path(document.storage_key).unlink(missing_ok=True)
    db.delete(document)
    db.commit()
    return Response(status_code=204)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> DocumentResponse:  # noqa: B008
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user.id))
    if document is None:
        raise AppError(404, "not_found", "Resource not found")
    job = db.scalar(select(Job).where(Job.document_id == document.id, Job.user_id == user.id).order_by(Job.created_at.desc()))
    if job is None:
        raise AppError(404, "not_found", "Resource not found")
    return _response(document, job)
