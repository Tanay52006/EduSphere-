from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import Settings
from app.main import create_app
from app.models.library import Chunk, Document, Job
from app.repos.keyword_store import SQLiteKeywordStore
from app.repos.vector_store import SQLiteVectorStore
from app.workers.process import create_sync_embedder, process_one
from app.workers.runner import IngestionJobRunner

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "pdfs"


@pytest.fixture
async def worker_client(tmp_path: Path) -> AsyncClient:
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'worker.db'}", storage_dir=str(tmp_path), auto_create_tables=True))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


async def upload(client: AsyncClient, filename: str) -> str:
    await client.post("/api/auth/signup", json={"email": f"{filename}@example.com", "password": "correct horse"})
    response = await client.post(
        "/api/documents",
        headers={"X-CSRF-Token": client.cookies["edu_csrf"]},
        files={"file": (filename, (FIXTURES / filename).read_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_runner_extracts_chunks_and_marks_document_ready(worker_client: AsyncClient) -> None:
    document_id = await upload(worker_client, "lecture-notes.pdf")
    app = worker_client._transport.app  # type: ignore[attr-defined]
    with app.state.session_local() as db:  # type: ignore[attr-defined]
        assert IngestionJobRunner().process_next(db, embed_text=lambda text: [float(len(text)), 0.0, 0.0]) is True
        document = db.scalar(select(Document).where(Document.id == document_id))
        job = db.scalar(select(Job).where(Job.document_id == document_id))
        chunks = db.scalars(select(Chunk).where(Chunk.document_id == document_id, Chunk.user_id == document.user_id)).all()
        assert document is not None and job is not None
        assert document.status == "ready"
        assert job.status == "succeeded" and job.progress == 100
        assert len(chunks) > 0
        assert SQLiteKeywordStore(db).search(document.user_id, "cellular respiration")
        assert SQLiteVectorStore(db, dimensions=3).query(document.user_id, [1.0, 0.0, 0.0])


@pytest.mark.asyncio
async def test_runner_marks_scanned_document_as_ocr_required(worker_client: AsyncClient) -> None:
    document_id = await upload(worker_client, "scanned-notes.pdf")
    app = worker_client._transport.app  # type: ignore[attr-defined]
    with app.state.session_local() as db:  # type: ignore[attr-defined]
        assert IngestionJobRunner().process_next(db) is True
        document = db.scalar(select(Document).where(Document.id == document_id))
        job = db.scalar(select(Job).where(Job.document_id == document_id))
        assert document is not None and job is not None
        assert document.status == "ocr_required" and document.ocr_required is True
        assert job.status == "succeeded"


@pytest.mark.asyncio
async def test_runner_fails_safely_when_file_is_missing(worker_client: AsyncClient) -> None:
    document_id = await upload(worker_client, "lecture-notes.pdf")
    app = worker_client._transport.app  # type: ignore[attr-defined]
    with app.state.session_local() as db:  # type: ignore[attr-defined]
        document = db.scalar(select(Document).where(Document.id == document_id))
        assert document is not None
        Path(document.storage_key).unlink()
        assert IngestionJobRunner().process_next(db) is True
        job = db.scalar(select(Job).where(Job.document_id == document_id))
        assert job is not None
        assert job.status == "failed" and job.error_code == "storage_unavailable"


@pytest.mark.asyncio
async def test_runner_cleans_derived_rows_when_embedding_fails(worker_client: AsyncClient) -> None:
    document_id = await upload(worker_client, "lecture-notes.pdf")
    app = worker_client._transport.app  # type: ignore[attr-defined]
    with app.state.session_local() as db:  # type: ignore[attr-defined]
        document = db.scalar(select(Document).where(Document.id == document_id))
        assert document is not None

        def fail_embedding(_: str) -> list[float]:
            raise ValueError("provider unavailable")

        assert IngestionJobRunner().process_next(db, embed_text=fail_embedding) is True
        db.expire_all()
        document = db.scalar(select(Document).where(Document.id == document_id))
        job = db.scalar(select(Job).where(Job.document_id == document_id))
        assert document is not None and job is not None
        assert document.status == "failed" and job.status == "failed"
        assert db.scalars(select(Chunk).where(Chunk.document_id == document_id)).all() == []
        assert SQLiteKeywordStore(db).search(document.user_id, "cellular respiration") == []
        assert SQLiteVectorStore(db, dimensions=3).query(document.user_id, [1.0, 0.0, 0.0]) == []


@pytest.mark.asyncio
async def test_process_one_uses_the_configured_session_factory(worker_client: AsyncClient) -> None:
    document_id = await upload(worker_client, "lecture-notes.pdf")
    app = worker_client._transport.app  # type: ignore[attr-defined]

    assert process_one(app.state.session_local) is True  # type: ignore[attr-defined]
    with app.state.session_local() as db:  # type: ignore[attr-defined]
        document = db.scalar(select(Document).where(Document.id == document_id))
        assert document is not None and document.status == "ready"


def test_sync_embedder_reuses_one_event_loop_for_a_provider() -> None:
    import asyncio

    loop_ids: list[int] = []

    class Provider:
        async def embed(self, _: str) -> list[float]:
            import asyncio

            loop_ids.append(id(asyncio.get_running_loop()))
            return [1.0]

    with asyncio.Runner() as runner:
        embed_text = create_sync_embedder(Provider(), runner)
        embed_text("first chunk")
        embed_text("second chunk")

    assert len(set(loop_ids)) == 1
