from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
async def chain(tmp_path: Path) -> Any:
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'chain.db'}",
                              storage_dir=str(tmp_path), auto_create_tables=True, llm_provider="mock"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        await client.post("/api/auth/signup", json={"email": "chain@example.com", "password": "correct horse"})
        client.headers["X-CSRF-Token"] = client.cookies["edu_csrf"]
        yield app, client


async def test_path_locking_feedback_completion_and_idempotent_xp(chain: Any) -> None:
    _, client = chain
    path = (await client.get("/api/chain")).json()
    assert len(path["levels"]) == 5
    assert path["levels"][0]["unlocked"] and not path["levels"][1]["unlocked"]
    assert (await client.post("/api/chain/start", json={"level_id": "build"})).status_code == 409
    reply = await client.post("/api/chain/start", json={"level_id": "spark"})
    assert reply.status_code == 201, reply.text
    game = reply.json()
    assert "solution" not in game and "expected" not in game
    assert next(n for n in game["nodes"] if n["id"] == "process")["kind"] == "slot"
    assert (await client.post("/api/chain/start", json={"level_id": "spark"})).json()["id"] == game["id"]
    endpoint = f"/api/chain/sessions/{game['id']}/run"
    wrong = await client.post(endpoint, json={"links": game["links"], "process": "digestion"})
    assert wrong.status_code == 200 and not wrong.json()["feedback"]["correct"]
    assert ["process", "atp"] not in wrong.json()["feedback"]["powered"]
    assert (await client.get("/api/progress")).json()["activities"] == 0
    assert (await client.post(endpoint, json={"links": [["invalid", "atp"]]})).status_code == 422
    assert (await client.post(endpoint, json={"links": [], "xp": 900})).status_code == 422
    solved = (await client.post(endpoint, json={"links": game["links"], "process": "respiration"})).json()
    assert solved["status"] == "completed" and solved["result"]["xp_earned"] > 0
    total = (await client.get("/api/progress")).json()["total_xp"]
    assert (await client.post(endpoint, json={"links": game["links"], "process": "respiration"})).json() == solved
    assert (await client.get("/api/progress")).json()["total_xp"] == total
    assert (await client.get("/api/chain")).json()["levels"][1]["unlocked"]
    assert (await client.get(f"/api/chain/sessions/{game['id']}")).json()["status"] == "completed"


async def test_chain_session_ownership_and_csrf(chain: Any) -> None:
    app, client = chain
    game = (await client.post("/api/chain/start", json={"level_id": "spark"})).json()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as other:
        assert (await other.get("/api/chain")).status_code == 401
        await other.post("/api/auth/signup", json={"email": "otherchain@example.com", "password": "correct horse"})
        assert (await other.post("/api/chain/start", json={"level_id": "spark"})).status_code == 403
        other.headers["X-CSRF-Token"] = other.cookies["edu_csrf"]
        assert (await other.get(f"/api/chain/sessions/{game['id']}")).status_code == 404
        assert (await other.post(f"/api/chain/sessions/{game['id']}/run", json={"links": []})).status_code == 404
        assert not (await other.get("/api/chain")).json()["levels"][0]["completed"]


async def test_all_authored_puzzles_have_valid_unique_solutions_and_award_once(chain: Any) -> None:
    from app.services.chain_levels import LEVELS

    _, client = chain
    for level in LEVELS:
        started = await client.post("/api/chain/start", json={"level_id": level["id"]})
        assert started.status_code == 201, started.text
        game = started.json()
        endpoint = f"/api/chain/sessions/{game['id']}/run"
        ids = {n["id"] for n in game["nodes"]}
        assert all(a in ids and b in ids and a != b for a, b in level["solution"])
        assert len(level["solution"]) == len(set(map(tuple, level["solution"])))
        bad = await client.post(endpoint, json={"links": [["atp", "atp"]]})
        assert bad.status_code == 422
        if level["id"] == "build":
            dry = [edge for edge in level["solution"] if edge != ["water", "photo"]]
            stopped = (await client.post(endpoint, json={"links": dry})).json()
            assert not stopped["feedback"]["correct"]
            assert stopped["feedback"]["stalled"] == "photo"
            assert "Water" in stopped["feedback"]["message"]
            assert ["photo", "fuel"] not in stopped["feedback"]["powered"]
            assert ["atp", "cell"] not in stopped["feedback"]["powered"]
        solved = await client.post(endpoint, json={"links": level["solution"], "process": "respiration",
                                                   "prediction": level.get("prediction_target")})
        assert solved.status_code == 200, solved.text
        assert solved.json()["status"] == "completed"
    assert all(level["completed"] for level in (await client.get("/api/chain")).json()["levels"])
    assert (await client.get("/api/progress")).json()["activities"] == 5


async def test_oxygen_requires_a_validated_prediction_as_well_as_a_working_pathway(chain: Any) -> None:
    from app.services.chain_levels import LEVELS

    _, client = chain
    for level in LEVELS[:2]:
        game = (await client.post("/api/chain/start", json={"level_id": level["id"]})).json()
        await client.post(f"/api/chain/sessions/{game['id']}/run", json={"links": level["solution"], "process": "respiration"})
    game = (await client.post("/api/chain/start", json={"level_id": "oxygen"})).json()
    assert game["prediction_prompt"] and "prediction_target" not in game
    endpoint = f"/api/chain/sessions/{game['id']}/run"
    total = (await client.get("/api/progress")).json()["total_xp"]
    missing = (await client.post(endpoint, json={"links": LEVELS[2]["solution"]})).json()
    assert missing["status"] == "open" and not missing["feedback"]["correct"]
    invalid = await client.post(endpoint, json={"links": LEVELS[2]["solution"], "prediction": "not-a-station"})
    assert invalid.status_code == 422
    wrong = (await client.post(endpoint, json={"links": LEVELS[2]["solution"], "prediction": "fermentation"})).json()
    assert wrong["status"] == "open" and not wrong["feedback"]["correct"]
    assert (await client.get("/api/progress")).json()["total_xp"] == total
    resumed = (await client.get(f"/api/chain/sessions/{game['id']}")).json()
    assert resumed["prediction"] == "fermentation"
    solved = (await client.post(endpoint, json={"links": LEVELS[2]["solution"], "prediction": "glycolysis"})).json()
    assert solved["status"] == "completed"
    assert solved["result"]["xp_earned"] > 0
