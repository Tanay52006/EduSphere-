from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.library import Chunk, Document, Job
from app.repos.keyword_store import SQLiteKeywordStore
from app.repos.vector_store import SQLiteVectorStore
from app.services.ingestion import IngestionError, chunk_pages, extract_pages


class IngestionJobRunner:
    """Process one durable ingestion job without exposing document contents."""

    def process_next(self, db: Session, embed_text: Callable[[str], list[float]] | None = None) -> bool:
        job = db.scalar(select(Job).where(Job.status == "queued").order_by(Job.created_at, Job.id))
        if job is None:
            return False
        job.status = "running"
        job.started_at = datetime.now(UTC)
        job.progress = 5
        db.commit()
        document = db.scalar(select(Document).where(Document.id == job.document_id, Document.user_id == job.user_id))
        if document is None or job.document_id is None:
            self._fail(db, job, None, "document_not_found")
            return True
        try:
            pages, ocr_required = extract_pages(Path(document.storage_key).read_bytes())
            job.progress = 50
            db.commit()
            chunks = chunk_pages(pages)
            keyword_store = SQLiteKeywordStore(db)
            keyword_store.ensure_schema()
            embedder = embed_text
            vector_store = SQLiteVectorStore(db) if embedder is not None else None
            for chunk in chunks:
                db_chunk = Chunk(
                    user_id=job.user_id,
                    document_id=document.id,
                    ordinal=chunk.ordinal,
                    text=chunk.text,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    token_count=chunk.token_count,
                )
                db.add(db_chunk)
                db.flush()
                keyword_store.index_chunk(db_chunk)
                if vector_store is not None and embedder is not None:
                    vector_store.add(
                        document.id,
                        job.user_id,
                        embedder(chunk.text),
                        {"chunk_id": db_chunk.id, "page_start": chunk.page_start, "page_end": chunk.page_end},
                    )
            document.page_count = len(pages)
            document.ocr_required = ocr_required
            document.status = "ocr_required" if ocr_required else "ready"
            job.status = "succeeded"
            job.progress = 100
            job.finished_at = datetime.now(UTC)
            db.commit()
        except IngestionError as exc:
            self._fail(db, job, document, exc.code)
        except (OSError, ValueError):
            self._fail(db, job, document, "storage_unavailable")
        except Exception:
            self._fail(db, job, document, "embedding_failed")
        return True

    @staticmethod
    def _fail(db: Session, job: Job, document: Document | None, error_code: str) -> None:
        db.rollback()
        if document is not None:
            keyword_store = SQLiteKeywordStore(db)
            keyword_store.ensure_schema()
            keyword_store.delete_by_document(job.user_id, document.id)
            SQLiteVectorStore(db).delete_by_document(job.user_id, document.id)
            db.execute(delete(Chunk).where(Chunk.user_id == job.user_id, Chunk.document_id == document.id))
        job.status = "failed"
        job.error_code = error_code
        job.finished_at = datetime.now(UTC)
        if document is not None:
            document.status = "failed"
            document.error_code = error_code
        db.commit()
