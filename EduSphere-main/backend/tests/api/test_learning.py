from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import Settings
from app.main import create_app
from app.models.auth import User
from app.models.library import Chunk, Document


@pytest.fixture
async def learning(tmp_path: Path) -> Any:
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'learning.db'}", storage_dir=str(tmp_path), auto_create_tables=True))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        await client.post("/api/auth/signup", json={"email": "learner@example.com", "password": "correct horse"})
        client.headers["X-CSRF-Token"] = client.cookies["edu_csrf"]
        with app.state.session_local() as db:
            user = db.scalar(select(User))
            document = Document(user_id=user.id, original_filename="Biology.pdf", storage_key="test-only.pdf", content_hash="a" * 64,
                                mime_type="application/pdf", size_bytes=1000, page_count=4, status="ready")
            db.add(document)
            db.flush()
            terms = ["Mitochondria", "Nucleus", "Ribosome", "Membrane", "Cytoplasm", "Chloroplast", "Vacuole", "Lysosome",
                     "Enzyme", "Glucose", "Osmosis", "Diffusion", "Protein", "Chromosome", "Photosynthesis", "Respiration",
                     "ATP", "DNA", "RNA", "Cellulose", "Chlorophyll", "Stomata", "Xylem", "Phloem"]
            text = "\n".join(f"{term} is the biological concept numbered {i}, with a distinct role in cellular function." for i, term in enumerate(terms))
            db.add(Chunk(user_id=user.id, document_id=document.id, ordinal=0, text=text, page_start=1, page_end=4, token_count=500))
            db.commit()
            document_id = document.id
        yield app, client, document_id


async def bank(client: AsyncClient, document_id: str) -> list[dict[str, Any]]:
    response = await client.post(f"/api/documents/{document_id}/questions/generate")
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["accepted"] >= 20
    assert data["pass_rate"] >= 0.85
    return (await client.get(f"/api/documents/{document_id}/questions")).json()["questions"]


async def test_generation_grounding_edit_flag_and_ownership(learning: Any) -> None:
    app, client, document_id = learning
    questions = await bank(client, document_id)
    assert all(q["sources"][0]["page_start"] == 1 for q in questions)
    question = questions[0]
    edited = await client.patch(f"/api/questions/{question['id']}", json={"prompt": "Edited prompt"})
    assert edited.status_code == 200
    assert edited.json()["validated"] is False
    await client.post(f"/api/questions/{questions[1]['id']}/flag")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as other:
        await other.post("/api/auth/signup", json={"email": "other@example.com", "password": "correct horse"})
        other.headers["X-CSRF-Token"] = other.cookies["edu_csrf"]
        for path, method in [(f"/documents/{document_id}/questions", "get"), (f"/questions/{question['id']}", "delete"),
                             (f"/questions/{question['id']}/flag", "post"), (f"/documents/{document_id}/questions/generate", "post"),
                             (f"/documents/{document_id}/file", "get")]:
            assert (await getattr(other, method)("/api" + path)).status_code == 404
        assert (await other.post("/api/games/sessions", json={"document_id": document_id, "game": "quiz_blitz"})).status_code == 404


async def test_quiz_scores_on_server_and_submission_is_idempotent(learning: Any) -> None:
    app, client, document_id = learning
    questions = await bank(client, document_id)
    answers = {q["id"]: q["answer"] for q in questions}
    started = await client.post("/api/games/sessions", json={"document_id": document_id, "game": "quiz_blitz"})
    assert started.status_code == 201, started.text
    session = started.json()
    session_id = session["id"]
    assert "answer" not in str(session)
    assert (await client.post(f"/api/games/sessions/{session_id}/submit", json={"score": 9999})).status_code == 422
    assert (await client.post(f"/api/games/sessions/{session_id}/submit", json={})).status_code == 409
    for _ in range(10):
        if session["index"]:
            session = (await client.post(f"/api/games/sessions/{session_id}/next", json={})).json()
        question = session["question"]
        reply = await client.post(f"/api/games/sessions/{session_id}/answer", json={"question_id": question["id"], "choice": answers[question["id"]]})
        assert reply.status_code == 200, reply.text
        session = reply.json()
    assert session["status"] == "finished"
    response = await client.post(f"/api/games/sessions/{session_id}/submit", json={})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["correct"] == 10 and result["xp_earned"] > 0
    assert (await client.post(f"/api/games/sessions/{session_id}/submit", json={})).json() == result
    assert (await client.get("/api/progress")).json()["total_xp"] == result["progress"]["total_xp"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as other:
        await other.post("/api/auth/signup", json={"email": "intruder@example.com", "password": "correct horse"})
        other.headers["X-CSRF-Token"] = other.cookies["edu_csrf"]
        endpoints = [("", "get"), ("/submit", "post"), ("/answer", "post"), ("/flip", "post"),
                     ("/next", "post"), ("/clock", "post"), ("/abandon", "post")]
        for suffix, method in endpoints:
            payload = {"question_id": "x", "choice": "x"} if suffix == "/answer" else {"card_id": "x"} if suffix == "/flip" else {}
            if suffix == "/clock":
                payload = {"paused": True}
            response = await getattr(other, method)(f"/api/games/sessions/{session_id}{suffix}", **({"json": payload} if method == "post" else {}))
            assert response.status_code == 404


async def test_memory_hides_cards_and_checks_matches_on_server(learning: Any) -> None:
    app, client, document_id = learning
    await bank(client, document_id)
    session = (await client.post("/api/games/sessions", json={"document_id": document_id, "game": "memory_match"})).json()
    assert len(session["cards"]) == 12
    assert all(card["text"] is None for card in session["cards"])
    from app.models.learning import GameSession

    with app.state.session_local() as db:
        state = db.get(GameSession, session["id"]).state
        pairs: dict[str, list[str]] = {}
        for card in state["cards"]:
            pairs.setdefault(card["pair"], []).append(card["id"])
    for ids in pairs.values():
        for card_id in ids:
            response = await client.post(f"/api/games/sessions/{session['id']}/flip", json={"card_id": card_id})
            assert response.status_code == 200, response.text
            session = response.json()
    result = (await client.post(f"/api/games/sessions/{session['id']}/submit", json={})).json()
    assert result["correct"] == 6 and result["moves"] == 6
    assert len(result["review"]) == 6 and result["review"][0]["sources"]


async def test_expired_round_and_no_csrf_cannot_award_points(learning: Any) -> None:
    app, client, document_id = learning
    await bank(client, document_id)
    session = (await client.post("/api/games/sessions", json={"document_id": document_id, "game": "quiz_blitz"})).json()
    from app.models.learning import GameSession

    with app.state.session_local() as db:
        row = db.get(GameSession, session["id"])
        row.state = {**row.state, "round_started": (datetime.now(UTC) - timedelta(seconds=40)).isoformat()}
        db.commit()
    response = await client.post(f"/api/games/sessions/{session['id']}/answer", json={"question_id": session["question"]["id"], "choice": "0"})
    assert response.json()["feedback"]["timed_out"] is True
    assert response.json()["correct"] == 0
    client.headers.pop("X-CSRF-Token")
    assert (await client.post(f"/api/documents/{document_id}/questions/generate")).status_code == 403


async def test_invalid_provider_fails_closed_and_retries_once(learning: Any) -> None:
    app, client, document_id = learning
    class InvalidProvider:
        calls = 0

        async def generate_json(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            self.calls += 1
            return {"questions": [{"prompt": "unsafe"}]}

    provider = InvalidProvider()
    app.state.llm_provider = provider
    response = await client.post(f"/api/documents/{document_id}/questions/generate")
    assert response.status_code == 502
    assert provider.calls == 2
    assert (await client.get(f"/api/documents/{document_id}/questions")).json()["questions"] == []


async def test_generation_budget_and_duplicate_suppression(learning: Any) -> None:
    _, client, document_id = learning
    await bank(client, document_id)
    for _ in range(4):
        reply = await client.post(f"/api/documents/{document_id}/questions/generate")
        assert reply.status_code == 201
        assert reply.json()["added"] == 0
    assert (await client.post(f"/api/documents/{document_id}/questions/generate")).status_code == 429
    assert len((await client.get(f"/api/documents/{document_id}/questions")).json()["questions"]) == 24


async def test_quiz_pause_and_feedback_do_not_spend_next_round_time(learning: Any) -> None:
    from app.models.learning import GameSession

    app, client, document_id = learning
    questions = await bank(client, document_id)
    answers = {q["id"]: q["answer"] for q in questions}
    session = (await client.post("/api/games/sessions", json={"document_id": document_id, "game": "quiz_blitz"})).json()
    base = f"/api/games/sessions/{session['id']}"
    assert (await client.post(base + "/clock", json={"paused": True})).json()["paused"] is True
    q = session["question"]
    assert (await client.post(base + "/answer", json={"question_id": q["id"], "choice": answers[q["id"]]})).status_code == 409
    await client.post(base + "/clock", json={"paused": False})
    answered = (await client.post(base + "/answer", json={"question_id": q["id"], "choice": answers[q["id"]]})).json()
    assert "question" not in answered and answered["feedback"]["correct"]
    assert (await client.post(base + "/clock", json={"paused": True})).json()["paused"] is False
    assert (await client.post(base + "/answer", json={"question_id": q["id"], "choice": answers[q["id"]]})).status_code == 409
    with app.state.session_local() as db:
        row = db.get(GameSession, session["id"])
        row.state = {**row.state, "round_started": (datetime.now(UTC) - timedelta(minutes=5)).isoformat()}
        db.commit()
    next_round = (await client.post(base + "/next", json={})).json()
    assert next_round["deadline"] > datetime.now(UTC).timestamp() + 28


async def test_real_pdf_upload_to_twenty_validated_questions(learning: Any) -> None:
    from app.workers.runner import IngestionJobRunner

    app, client, _ = learning
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "pdfs" / "biology-glossary.pdf"
    response = await client.post("/api/documents", files={"file": ("biology.pdf", fixture.read_bytes(), "application/pdf")})
    assert response.status_code == 201
    document_id = response.json()["id"]
    with app.state.session_local() as db:
        assert IngestionJobRunner().process_next(db, embed_text=lambda _: [0.0, 0.0, 0.0])
    questions = await bank(client, document_id)
    assert len(questions) == 24
    assert sum(q["kind"] == "MCQ" for q in questions) == 16
    assert sum(q["kind"] == "MATCH" for q in questions) == 8
    source = await client.get(f"/api/documents/{document_id}/file")
    assert source.status_code == 200 and source.headers["content-type"] == "application/pdf"


@pytest.mark.parametrize("forged_sources", [True, False])
async def test_untrusted_sources_and_rejected_verdicts_never_enter_games(learning: Any, forged_sources: bool) -> None:
    from app.ai.mock import MockProvider

    class RejectedProvider(MockProvider):
        async def generate_json(self, schema: Any, prompt: str, **kwargs: Any) -> dict[str, Any]:
            result = await super().generate_json(schema, prompt, **kwargs)
            if forged_sources and schema.__name__ == "GeneratedQuestions":
                for question in result["questions"]:
                    question["source_chunk_id"] = "another-users-chunk"
            if not forged_sources and schema.__name__ == "ValidatedQuestions":
                for verdict in result["verdicts"]:
                    verdict["supported"] = False
            return result

    app, client, document_id = learning
    app.state.llm_provider = RejectedProvider()
    response = await client.post(f"/api/documents/{document_id}/questions/generate")
    assert response.status_code == (422 if forged_sources else 201)
    assert (await client.get(f"/api/documents/{document_id}/questions")).json()["questions"] == []


async def test_validation_batches_use_local_indices_and_reject_missing_or_duplicate_verdicts(learning: Any) -> None:
    import json

    from app.ai.mock import MockProvider

    batch_sizes = []

    class BatchedProvider(MockProvider):
        async def generate_json(self, schema: Any, prompt: str, **kwargs: Any) -> dict[str, Any]:
            result = await super().generate_json(schema, prompt, **kwargs)
            if schema.__name__ == "ValidatedQuestions":
                payload = json.loads(next(line for line in prompt.splitlines() if line.startswith('{"quoted_sources"')))
                batch_sizes.append(len(payload["proposals"]))
                if len(batch_sizes) == 2:
                    result["verdicts"] = [{"index": 0, "supported": False}, {"index": 1, "supported": True},
                                          {"index": 1, "supported": True}, *result["verdicts"][3:]]
            return result

    app, client, document_id = learning
    app.state.llm_provider = BatchedProvider()
    result = await client.post(f"/api/documents/{document_id}/questions/generate")
    assert result.status_code == 201
    assert batch_sizes == [8, 8, 8]
    assert result.json()["accepted"] == 21
    questions = (await client.get(f"/api/documents/{document_id}/questions")).json()["questions"]
    assert len(questions) == 21
