from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import Settings
from app.main import create_app
from app.models.library import Document, Job
from app.workers.runner import IngestionJobRunner

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "pdfs" / "lecture-notes.pdf"


@pytest.fixture
async def document_client(tmp_path: Path) -> AsyncClient:
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'documents.db'}", storage_dir=str(tmp_path), auto_create_tables=True))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


async def signup(client: AsyncClient, email: str) -> None:
    response = await client.post("/api/auth/signup", json={"email": email, "password": "correct horse"})
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_upload_creates_user_scoped_document_and_queued_job(document_client: AsyncClient) -> None:
    await signup(document_client, "alice@example.com")
    csrf = document_client.cookies["edu_csrf"]

    response = await document_client.post(
        "/api/documents",
        headers={"X-CSRF-Token": csrf},
        files={"file": ("lecture-notes.pdf", FIXTURE.read_bytes(), "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "queued"
    assert body["original_filename"] == "lecture-notes.pdf"
    assert body["job_id"]
    app = document_client._transport.app  # type: ignore[attr-defined]
    with app.state.session_local() as db:  # type: ignore[attr-defined]
        document = db.scalar(select(Document))
        job = db.scalar(select(Job))
        assert document is not None and job is not None
        assert document.user_id == job.user_id
        assert job.document_id == document.id
        assert Path(document.storage_key).exists()


@pytest.mark.asyncio
async def test_upload_rejects_invalid_pdf_without_storage(document_client: AsyncClient) -> None:
    await signup(document_client, "alice@example.com")
    csrf = document_client.cookies["edu_csrf"]

    response = await document_client.post(
        "/api/documents",
        headers={"X-CSRF-Token": csrf},
        files={"file": ("notes.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_pdf_type"


@pytest.mark.asyncio
async def test_upload_requires_csrf(document_client: AsyncClient) -> None:
    await signup(document_client, "alice@example.com")

    response = await document_client.post(
        "/api/documents",
        files={"file": ("lecture-notes.pdf", FIXTURE.read_bytes(), "application/pdf")},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_reports_quota_and_page_limit_errors_safely(document_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    await signup(document_client, "limits@example.com")
    csrf = document_client.cookies["edu_csrf"]
    monkeypatch.setattr("app.services.ingestion.MAX_USER_BYTES", 1)

    quota_response = await document_client.post(
        "/api/documents",
        headers={"X-CSRF-Token": csrf},
        files={"file": ("lecture-notes.pdf", FIXTURE.read_bytes(), "application/pdf")},
    )

    assert quota_response.status_code == 413
    assert quota_response.json()["error"] == {
        "code": "user_quota_exceeded",
        "message": "The PDF could not be accepted",
    }
    monkeypatch.setattr("app.services.ingestion.MAX_USER_BYTES", 100 * 1024 * 1024)
    monkeypatch.setattr("app.services.ingestion.MAX_DOCUMENT_PAGES", 1)

    page_response = await document_client.post(
        "/api/documents",
        headers={"X-CSRF-Token": csrf},
        files={"file": ("lecture-notes.pdf", FIXTURE.read_bytes(), "application/pdf")},
    )

    assert page_response.status_code == 413
    assert page_response.json()["error"]["code"] == "page_limit_exceeded"


@pytest.mark.asyncio
async def test_document_list_and_detail_are_user_scoped(document_client: AsyncClient) -> None:
    await signup(document_client, "alice@example.com")
    alice_csrf = document_client.cookies["edu_csrf"]
    uploaded = await document_client.post(
        "/api/documents",
        headers={"X-CSRF-Token": alice_csrf},
        files={"file": ("lecture-notes.pdf", FIXTURE.read_bytes(), "application/pdf")},
    )
    document_id = uploaded.json()["id"]
    app = document_client._transport.app  # type: ignore[attr-defined]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as bob:
        await signup(bob, "bob@example.com")
        assert (await bob.get("/api/documents")).json() == []
        hidden = await bob.get(f"/api/documents/{document_id}")
        assert hidden.status_code == 404

    listed = await document_client.get("/api/documents")
    assert [item["id"] for item in listed.json()] == [document_id]
    detail = await document_client.get(f"/api/documents/{document_id}")
    assert detail.status_code == 200
    assert detail.json()["job_id"] == uploaded.json()["job_id"]


@pytest.mark.asyncio
async def test_document_list_reports_safe_ingestion_error_code(document_client: AsyncClient) -> None:
    await signup(document_client, "failed@example.com")
    csrf = document_client.cookies["edu_csrf"]
    uploaded = await document_client.post(
        "/api/documents",
        headers={"X-CSRF-Token": csrf},
        files={"file": ("lecture-notes.pdf", FIXTURE.read_bytes(), "application/pdf")},
    )
    document_id = uploaded.json()["id"]
    app = document_client._transport.app  # type: ignore[attr-defined]
    with app.state.session_local() as db:  # type: ignore[attr-defined]
        assert IngestionJobRunner().process_next(db, embed_text=lambda _: (_ for _ in ()).throw(RuntimeError())) is True

    listed = await document_client.get("/api/documents")

    assert listed.status_code == 200
    failed = next(item for item in listed.json() if item["id"] == document_id)
    assert failed["status"] == "failed"
    assert failed["error_code"] == "embedding_failed"


@pytest.mark.asyncio
async def test_document_delete_removes_owned_file_and_derived_rows(document_client: AsyncClient) -> None:
    await signup(document_client, "alice@example.com")
    csrf = document_client.cookies["edu_csrf"]
    uploaded = await document_client.post(
        "/api/documents",
        headers={"X-CSRF-Token": csrf},
        files={"file": ("lecture-notes.pdf", FIXTURE.read_bytes(), "application/pdf")},
    )
    document_id = uploaded.json()["id"]
    app = document_client._transport.app  # type: ignore[attr-defined]
    with app.state.session_local() as db:  # type: ignore[attr-defined]
        document = db.scalar(select(Document).where(Document.id == document_id))
        assert document is not None
        stored_path = Path(document.storage_key)

    response = await document_client.delete(
        f"/api/documents/{document_id}", headers={"X-CSRF-Token": csrf}
    )

    assert response.status_code == 204
    assert not stored_path.exists()
    assert (await document_client.get(f"/api/documents/{document_id}")).status_code == 404


@pytest.mark.asyncio
async def test_document_delete_is_user_scoped(document_client: AsyncClient) -> None:
    await signup(document_client, "alice@example.com")
    csrf = document_client.cookies["edu_csrf"]
    uploaded = await document_client.post(
        "/api/documents",
        headers={"X-CSRF-Token": csrf},
        files={"file": ("lecture-notes.pdf", FIXTURE.read_bytes(), "application/pdf")},
    )
    document_id = uploaded.json()["id"]
    app = document_client._transport.app  # type: ignore[attr-defined]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as bob:
        await signup(bob, "bob@example.com")
        response = await bob.delete(
            f"/api/documents/{document_id}", headers={"X-CSRF-Token": bob.cookies["edu_csrf"]}
        )

    assert response.status_code == 404
    assert (await document_client.get(f"/api/documents/{document_id}")).status_code == 200
