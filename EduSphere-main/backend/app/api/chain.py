from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics import wrapper as analytics
from app.api.dependencies import get_current_user
from app.core.db import get_db
from app.core.errors import AppError
from app.models.auth import User
from app.models.learning import GameSession
from app.services.chain_levels import LEVELS, level_by_id
from app.services.games import lock_user, open_session, owned_session
from app.services.progress import award_game, summary

router = APIRouter(prefix="/chain", tags=["chain-reaction"])


class StartChain(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level_id: str = Field(max_length=32)


class RunChain(BaseModel):
    model_config = ConfigDict(extra="forbid")
    links: list[tuple[str, str]] = Field(max_length=24)
    process: str | None = Field(default=None, max_length=32)
    prediction: str | None = Field(default=None, max_length=32)


def completed_levels(db: Session, user: User) -> set[str]:
    return {s.state["level_id"] for s in db.scalars(select(GameSession).where(
        GameSession.user_id == user.id, GameSession.game == "chain_reaction", GameSession.status == "completed"))}


def view(session: GameSession) -> dict[str, Any]:
    level = level_by_id(session.state["level_id"])
    assert level is not None
    if level["mode"] == "place":
        for node in level["nodes"]:
            if node["id"] == "process":
                node.update(label="Missing process", kind="slot")
    return {"id": session.id, "status": session.status, "level_id": level["id"], "title": level["title"],
            "goal": level["goal"], "mode": level["mode"], "hint": level["hint"], "nodes": level["nodes"],
            "choices": level.get("choices", []), "source": level["source"], "links": session.state["links"],
            "process": session.state.get("process"), "attempts": session.state["moves"],
            "prediction_prompt": level.get("prediction_prompt"), "prediction_options": level.get("prediction_options", []),
            "prediction": session.state.get("prediction"),
            "feedback": session.state.get("feedback"), "result": session.result}


@router.get("")
def journey(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    done = completed_levels(db, user)
    return {"chapter": "Energy of life", "subject": "Biology", "levels": [
        {"id": level["id"], "title": level["title"], "icon": level["icon"], "mode": level["mode"],
         "completed": level["id"] in done, "unlocked": i == 0 or LEVELS[i - 1]["id"] in done}
        for i, level in enumerate(LEVELS)], "progress": summary(db, user)}


@router.post("/start", status_code=201)
def start(payload: StartChain, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    lock_user(db, user)
    level = level_by_id(payload.level_id)
    if level is None:
        raise AppError(404, "not_found", "Chapter not found.")
    index = next(i for i, item in enumerate(LEVELS) if item["id"] == payload.level_id)
    if index and LEVELS[index - 1]["id"] not in completed_levels(db, user):
        raise AppError(409, "level_locked", "Complete the previous stop to unlock this one.")
    now = datetime.now(UTC)
    for old in db.scalars(select(GameSession).where(GameSession.user_id == user.id,
                         GameSession.game == "chain_reaction", GameSession.status == "open")):
        if old.state["level_id"] == payload.level_id:
            if (now - old.started_at.replace(tzinfo=UTC)).total_seconds() <= 3600:
                db.commit()
                return view(old)
            old.status = "abandoned"
    state = {"level_id": level["id"], "links": level["initial"], "process": None, "moves": 0,
             "fingerprint": f"energy-v1:{level['id']}", "questions": [{"id": level["id"]}],
             "index": 0, "correct": 0, "lives": 0, "combo": 0, "score": 0, "history": []}
    session = GameSession(user_id=user.id, document_id=None, game="chain_reaction", started_at=now, state=state)
    db.add(session)
    db.commit()
    analytics.track("Game Started", {"game": "chain_reaction", "level": level["id"]})
    return view(session)


def chain_session(db: Session, user: User, session_id: str) -> GameSession:
    session = owned_session(db, user, session_id)
    if session.game != "chain_reaction":
        raise AppError(404, "not_found", "Resource not found")
    return session


@router.get("/sessions/{session_id}")
def resume(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    return view(chain_session(db, user, session_id))


@router.post("/sessions/{session_id}/run")
def run(session_id: str, payload: RunChain, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    session = chain_session(db, user, session_id)
    if session.status == "completed":
        return view(session)
    open_session(session, "chain_reaction")
    level = level_by_id(session.state["level_id"])
    assert level is not None
    nodes = {n["id"]: n for n in level["nodes"]}
    links = set(payload.links)
    if len(links) != len(payload.links) or any(a not in nodes or b not in nodes or a == b for a, b in links):
        raise AppError(422, "invalid_links", "Choose two different stations on this board.")
    if any(not nodes[a]["output"] or not nodes[b]["input"] for a, b in links):
        raise AppError(422, "invalid_ports", "Connect an output to an input.")
    if payload.process is not None and payload.process not in {"respiration", "digestion", "fermentation"}:
        raise AppError(422, "invalid_process", "Choose a process from the tray.")
    if payload.prediction is not None and payload.prediction not in level.get("prediction_options", []):
        raise AppError(422, "invalid_prediction", "Choose a highlighted process station.")
    solution = set(map(tuple, level["solution"]))
    prediction_correct = not level.get("prediction_target") or payload.prediction == level["prediction_target"]
    correct = links == solution and (level["mode"] != "place" or payload.process == "respiration") and prediction_correct
    wrong = sorted(links - solution)
    missing = len(solution - links)
    message = ("This process cannot supply ATP from glucose and oxygen. Try another station." if level["mode"] == "place"
               else f"{nodes[wrong[0][0]]['label']} → {nodes[wrong[0][1]]['label']} does not belong in this pathway." if wrong
               else f"There {'is' if missing == 1 else 'are'} {missing} missing connection{'s' if missing != 1 else ''}.")
    stalled = "process" if level["mode"] == "place" else None
    if level["mode"] != "place" and missing and not wrong:
        stalled = next(n for n in nodes if any(b == n and (a, b) not in links for a, b in solution))
        inputs = [nodes[a]["label"] for a, b in sorted(solution - links) if b == stalled]
        message = f"{nodes[stalled]['label']} still needs {' and '.join(inputs)}. Trace the inputs to get it moving."
    elif links == solution and not prediction_correct:
        message = "The pathway is connected. Reconsider which process produces ATP; restoring NAD⁺ is a different job."
    # A station activates only after all its required inputs are supplied.
    requirements = {key: {a for a, b in solution if b == key} for key in nodes}
    active = {key for key, required in requirements.items() if not required} | ({"nad"} if "nad" in nodes else set())
    blocked = {"process"} if level["mode"] == "place" and payload.process != "respiration" else set()
    for _ in nodes:
        for key, required in requirements.items():
            if key not in blocked and required and all(a in active and (a, key) in links for a in required):
                active.add(key)
    powered = [list(edge) for edge in sorted(links & solution) if edge[0] in active and edge[0] not in blocked]
    state = {**session.state, "links": payload.links, "process": payload.process, "prediction": payload.prediction,
             "moves": session.state["moves"] + 1,
             "feedback": {"correct": correct, "message": level["explanation"] if correct else message,
                          "broken": wrong[0] if wrong else None, "powered": powered, "stalled": stalled if not correct else None}}
    session.state = state
    if correct:
        state["correct"] = 1
        state["score"] = 100
        xp = award_game(db, user, session, 1.0)
        session.status = "completed"
        db.flush()
        session.result = {"xp_earned": xp, "progress": summary(db, user)}
        analytics.track("Game Completed", {"game": "chain_reaction", "level": level["id"], "attempts": state["moves"], "xp_earned": xp})
    db.commit()
    return view(session)
