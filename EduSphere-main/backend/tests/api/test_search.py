from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app
from app.workers.runner import IngestionJobRunner

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "pdfs" / "lecture-notes.pdf"


@pytest.mark.asyncio
async def test_search_returns_hybrid_hits_and_is_user_scoped(tmp_path: Path) -> None:
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'search.db'}", storage_dir=str(tmp_path), auto_create_tables=True))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as alice:
        await alice.post("/api/auth/signup", json={"email": "alice@example.com", "password": "correct horse"})
        upload = await alice.post(
            "/api/documents",
            headers={"X-CSRF-Token": alice.cookies["edu_csrf"]},
            files={"file": ("lecture-notes.pdf", FIXTURE.read_bytes(), "application/pdf")},
        )
        assert upload.status_code == 201
        with app.state.session_local() as db:  # type: ignore[attr-defined]
            assert IngestionJobRunner().process_next(db, embed_text=lambda text: [1.0, 0.0, 0.0]) is True

        response = await alice.get("/api/search", params={"q": "cellular respiration"})
        assert response.status_code == 200
        assert response.json()["results"]
        assert "keyword" in response.json()["results"][0]["sources"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as bob:
        await bob.post("/api/auth/signup", json={"email": "bob@example.com", "password": "correct horse"})
        response = await bob.get("/api/search", params={"q": "cellular respiration"})
        assert response.status_code == 200
        assert response.json()["results"] == []
