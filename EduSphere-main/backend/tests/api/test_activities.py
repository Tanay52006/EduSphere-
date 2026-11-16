from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import Settings
from app.main import create_app
from app.models.auth import User
from app.models.library import Chunk, Document
from app.services.activity_catalog import CATALOG, authored


@pytest.fixture
async def activities(tmp_path: Path) -> Any:
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'activities.db'}",
                              storage_dir=str(tmp_path), auto_create_tables=True, llm_provider="mock"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        await client.post("/api/auth/signup", json={"email": "activities@example.com", "password": "correct horse"})
        client.headers["X-CSRF-Token"] = client.cookies["edu_csrf"]
        with app.state.session_local() as db:
            user = db.scalar(select(User))
            doc = Document(user_id=user.id, original_filename="lab.pdf", storage_key="test-only.pdf", content_hash="f" * 64,
                           mime_type="application/pdf", size_bytes=900, page_count=1, status="ready")
            db.add(doc)
            db.flush()
            db.add(Chunk(user_id=user.id, document_id=doc.id, ordinal=0, page_start=1, page_end=1, token_count=80,
                         text="Iron is an element containing one type of atom. Gold is an element containing one type of atom. "
                              "Water is a compound made from bonded elements. Salt is a compound made from bonded elements."))
            db.commit()
            doc_id = doc.id
        yield app, client, doc_id


async def test_every_subject_game_scores_saves_and_awards_once(activities: Any) -> None:
    _, client, _ = activities
    catalog = (await client.get("/api/activities")).json()
    assert len(catalog["activities"]) == 5
    for activity_id in CATALOG:
        content = authored(activity_id)["blueprint"]
        game = (await client.post("/api/activities/start", json={"activity_id": activity_id})).json()
        assert not {"explanation", "order", "assignments", "links"} & game["activity"].keys()
        assert all("source_quote" not in item for item in game["activity"]["items"])
        assert (await client.post("/api/activities/start", json={"activity_id": activity_id})).json()["id"] == game["id"]
        endpoint = f"/api/activities/sessions/{game['id']}/run"
        assert (await client.post(endpoint, json={"order": ["unknown"], "xp": 999})).status_code == 422
        public_ids = {item["label"]: item["id"] for item in game["activity"]["items"]}
        ids = {item["id"]: public_ids[item["label"]] for item in content["items"]}
        payload = {"order": [ids[key] for key in content["order"]],
                   "assignments": {ids[key]: value for key, value in content["assignments"].items()},
                   "links": [[ids[a], ids[b]] for a, b in content["links"]]}
        wrong = await client.post(endpoint, json={"order": list(reversed(payload["order"]))} if content["mechanic"] == "sequence" else {})
        assert wrong.status_code == 200 and wrong.json()["status"] == "open"
        solved = (await client.post(endpoint, json=payload)).json()
        assert solved["status"] == "completed" and solved["result"]["explanation"]
        total = (await client.get("/api/progress")).json()["total_xp"]
        assert (await client.post(endpoint, json=payload)).json() == solved
        assert (await client.get("/api/progress")).json()["total_xp"] == total
        assert (await client.get(f"/api/activities/sessions/{game['id']}")).json() == solved


async def test_generation_is_private_grounded_and_shares_the_quota(activities: Any) -> None:
    app, client, doc_id = activities
    response = await client.post("/api/activities/generate", json={"document_id": doc_id})
    assert response.status_code == 201, response.text
    card = response.json()
    assert card["preview"] and card["generated"]
    assert "assignments" not in card
    assert (await client.get(f"/api/documents/{doc_id}/questions")).json()["quality"] is None
    game = (await client.post("/api/activities/start", json={"activity_id": card["id"]})).json()
    assert game["sources"][0]["url"].endswith("#page=1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as other:
        assert (await other.get("/api/activities")).status_code == 401
        await other.post("/api/auth/signup", json={"email": "otheractivity@example.com", "password": "correct horse"})
        assert (await other.post("/api/activities/start", json={"activity_id": card["id"]})).status_code == 403
        other.headers["X-CSRF-Token"] = other.cookies["edu_csrf"]
        assert not any(a["id"] == card["id"] for a in (await other.get("/api/activities")).json()["activities"])
        for path, payload in [("/start", {"activity_id": card["id"]}), ("/generate", {"document_id": doc_id}),
                              (f"/sessions/{game['id']}/run", {})]:
            assert (await other.post("/api/activities" + path, json=payload)).status_code == 404
        assert (await other.get(f"/api/activities/sessions/{game['id']}")).status_code == 404
    for _ in range(4):
        assert (await client.post("/api/activities/generate", json={"document_id": doc_id})).status_code == 201
    assert (await client.post(f"/api/documents/{doc_id}/questions/generate")).status_code == 429
    assert (await client.post("/api/activities/generate", json={"document_id": doc_id})).status_code == 429


async def test_unverified_generation_fails_closed_and_deletion_removes_games(activities: Any) -> None:
    app, client, doc_id = activities
    original = app.state.llm_provider.generate_json

    async def reject(schema: Any, prompt: str, **kwargs: Any) -> Any:
        if schema.__name__ == "ActivityVerdict":
            return {"supported": False, "unambiguous": True, "appropriate": True}
        return await original(schema, prompt, **kwargs)

    app.state.llm_provider.generate_json = reject
    assert (await client.post("/api/activities/generate", json={"document_id": doc_id})).status_code == 422
    assert len((await client.get("/api/activities")).json()["activities"]) == 5
    app.state.llm_provider.generate_json = original
    card = (await client.post("/api/activities/generate", json={"document_id": doc_id})).json()
    game = (await client.post("/api/activities/start", json={"activity_id": card["id"]})).json()
    assert (await client.delete(f"/api/documents/{doc_id}")).status_code == 204
    assert (await client.post("/api/activities/start", json={"activity_id": card["id"]})).status_code == 404
    assert (await client.get(f"/api/activities/sessions/{game['id']}")).status_code == 404


async def test_fabricated_quotes_and_ambiguous_structures_are_rejected(activities: Any) -> None:
    from pydantic import ValidationError

    from app.schemas.activities import ActivityBlueprint

    app, client, doc_id = activities
    original = app.state.llm_provider.generate_json

    async def fabricate(schema: Any, prompt: str, **kwargs: Any) -> Any:
        data = await original(schema, prompt, **kwargs)
        if schema.__name__ == "ActivityProposal":
            data["activity"]["items"][0]["source_quote"] = "This sentence never appeared in the uploaded source."
        return data

    app.state.llm_provider.generate_json = fabricate
    response = await client.post("/api/activities/generate", json={"document_id": doc_id})
    assert response.status_code == 422 and response.json()["error"]["code"] == "ungrounded_game"
    broken = deepcopy(CATALOG["hydro-power"])
    broken.pop("source")
    broken["links"].append(("n4", "n1"))
    with pytest.raises(ValidationError):
        ActivityBlueprint.model_validate(broken)


async def test_focus_can_select_a_later_section_and_no_fit_is_not_invented(activities: Any) -> None:
    app, client, doc_id = activities
    with app.state.session_local() as db:
        user = db.scalar(select(User))
        for i in range(1, 10):
            db.add(Chunk(user_id=user.id, document_id=doc_id, ordinal=i, page_start=i + 1, page_end=i + 1,
                         token_count=20, text="Unrelated introductory material without a sequence or categories."))
        db.add(Chunk(user_id=user.id, document_id=doc_id, ordinal=10, page_start=11, page_end=11, token_count=90,
                     text="Laboratory procedure\n1. Prepare the sample\n2. Measure the sample\n3. Record the measurement\n4. Clean the equipment"))
        db.commit()
    generated = await client.post("/api/activities/generate", json={"document_id": doc_id, "focus": "Laboratory procedure"})
    assert generated.status_code == 201 and generated.json()["mechanic"] == "sequence"
    game = (await client.post("/api/activities/start", json={"activity_id": generated.json()["id"]})).json()
    assert game["sources"][0]["url"].endswith("#page=11")

    async def no_fit(*args: Any, **kwargs: Any) -> Any:
        return {"activity": None}

    app.state.llm_provider.generate_json = no_fit
    rejected = await client.post("/api/activities/generate", json={"document_id": doc_id})
    assert rejected.status_code == 422 and rejected.json()["error"]["code"] == "no_suitable_game"
