import hashlib
import json
import random
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.auth import User
from app.models.learning import GameSession, LearningActivity
from app.schemas.activities import RunActivity
from app.services.activity_catalog import authored
from app.services.games import lock_user, owned_session


def activity_card(activity_id: str, content: dict[str, Any], document_id: str | None = None) -> dict[str, Any]:
    b = content["blueprint"]
    return {"id": activity_id, "title": b["title"], "subject": b["subject"], "mechanic": b["mechanic"],
            "goal": b["goal"], "why_fit": b["why_fit"], "size": len(b["items"]), "generated": document_id is not None,
            "document_id": document_id, "preview": content["preview"]}


def find_activity(db: Session, user: User, activity_id: str) -> tuple[dict[str, Any], str | None]:
    content = authored(activity_id)
    if content:
        return content, None
    row = db.scalar(select(LearningActivity).where(LearningActivity.id == activity_id, LearningActivity.user_id == user.id))
    if row is None:
        raise AppError(404, "not_found", "Resource not found")
    return row.content, row.document_id


def start_activity(db: Session, user: User, activity_id: str) -> GameSession:
    lock_user(db, user)
    content, document_id = find_activity(db, user, activity_id)
    now = datetime.now(UTC)
    for old in db.scalars(select(GameSession).where(GameSession.user_id == user.id, GameSession.game == "activity", GameSession.status == "open")):
        if old.state["activity_id"] == activity_id:
            if (now - old.started_at.replace(tzinfo=UTC)).total_seconds() <= 3600:
                return old
            old.status = "abandoned"
    b = content["blueprint"]
    ids = [item["id"] for item in b["items"]]
    random.SystemRandom().shuffle(ids)
    if b["mechanic"] == "sequence" and ids == b["order"]:
        ids = ids[1:] + ids[:1]
    # Include the semantic task, not its generated ID/title, so duplicate drafts share replay decay.
    labels = {item["id"]: item["label"].casefold().strip() for item in b["items"]}
    groups = {bucket["id"]: bucket["label"].casefold().strip() for bucket in b["buckets"]}
    meaning = {"mechanic": b["mechanic"], "items": sorted(labels.values()), "order": [labels[key] for key in b["order"]],
               "assignments": sorted((labels[key], groups[value]) for key, value in b["assignments"].items()),
               "links": sorted((labels[a], labels[c]) for a, c in b["links"])}
    fingerprint = hashlib.sha256(json.dumps(meaning, sort_keys=True).encode()).hexdigest()
    # Shuffle identity separately from presentation so IDs cannot reveal a sequence answer.
    content = deepcopy(content)
    b = content["blueprint"]
    original_ids = [item["id"] for item in b["items"]]
    aliases = dict(zip(original_ids, random.SystemRandom().sample(original_ids, len(original_ids)), strict=True))
    for item in b["items"]:
        item["id"] = aliases[item["id"]]
    b["order"] = [aliases[key] for key in b["order"]]
    b["assignments"] = {aliases[key]: value for key, value in b["assignments"].items()}
    b["links"] = [[aliases[a], aliases[c]] for a, c in b["links"]]
    ids = [aliases[key] for key in ids]
    game = GameSession(user_id=user.id, document_id=document_id, game="activity", started_at=now,
                       state={"activity_id": activity_id, "content": content, "display": ids,
                              "draft": {"order": ids if b["mechanic"] == "sequence" else [], "assignments": {}, "links": []},
                              "moves": 0, "correct": 0, "score": 0, "questions": [{"id": activity_id}], "fingerprint": fingerprint})
    db.add(game)
    db.flush()
    return game


def activity_session(db: Session, user: User, session_id: str) -> GameSession:
    game = owned_session(db, user, session_id)
    if game.game != "activity":
        raise AppError(404, "not_found", "Resource not found")
    return game


def session_view(game: GameSession) -> dict[str, Any]:
    state = game.state
    b = state["content"]["blueprint"]
    by_id = {item["id"]: item["label"] for item in b["items"]}
    return {"id": game.id, "status": game.status, "activity_id": state["activity_id"],
            "activity": {**{key: b[key] for key in ("title", "subject", "mechanic", "goal", "why_fit", "buckets")},
                         "items": [{"id": key, "label": by_id[key]} for key in state["display"]]},
            "draft": state["draft"], "attempts": state["moves"], "feedback": state.get("feedback"), "result": game.result,
            "sources": state["content"]["sources"], "preview": state["content"]["preview"]}


def score_activity(game: GameSession, payload: RunActivity) -> dict[str, Any]:
    b = game.state["content"]["blueprint"]
    items = {item["id"]: item["label"] for item in b["items"]}
    ids = set(items)
    mode = b["mechanic"]
    if any(key not in ids for key in payload.order + list(payload.assignments) + [n for edge in payload.links for n in edge]):
        raise AppError(422, "invalid_card", "Use cards from this board.")
    if (mode != "sequence" and payload.order) or (mode != "sort" and payload.assignments) or (mode != "connections" and payload.links):
        raise AppError(422, "wrong_mechanic", "Use this game's controls.")
    misplaced: list[str] = []
    broken = None
    powered: list[list[str]] = []
    message = "Place every card, then check your solution."
    if mode == "sequence":
        if len(payload.order) != len(ids) or set(payload.order) != ids:
            raise AppError(422, "invalid_order", "Use each card exactly once.")
        misplaced = [key for i, key in enumerate(payload.order) if key != b["order"][i]]
        correct = not misplaced
        if misplaced:
            ranks = {key: i for i, key in enumerate(b["order"])}
            a, c = next((a, c) for a, c in zip(payload.order, payload.order[1:], strict=False) if ranks[a] > ranks[c])
            message = f"{items[c]} belongs before {items[a]}. Rebuild that part of the sequence."
    elif mode == "sort":
        buckets = {bucket["id"]: bucket for bucket in b["buckets"]}
        if any(value not in buckets for value in payload.assignments.values()):
            raise AppError(422, "invalid_group", "Choose a group on this board.")
        misplaced = [key for key, value in payload.assignments.items() if b["assignments"][key] != value]
        correct = len(payload.assignments) == len(ids) and not misplaced
        if misplaced:
            wrong = misplaced[0]
            group = buckets[payload.assignments[wrong]]
            message = f"Reconsider {items[wrong]}. {group['label']}: {group['rule']}"
    else:
        links = set(payload.links)
        if len(links) != len(payload.links) or any(a == c for a, c in links):
            raise AppError(422, "invalid_links", "Use distinct stations and connections.")
        expected = set(map(tuple, b["links"]))
        correct = links == expected
        wrong_links = sorted(links - expected)
        if wrong_links:
            broken = list(wrong_links[0])
            message = f"Reconsider {items[broken[0]]} → {items[broken[1]]}. Follow the stated relationship, one step at a time."
        elif expected - links:
            message = f"{len(expected - links)} connection(s) still missing. Trace the next stage of the system."
        powered = [list(edge) for edge in sorted(links & expected)]
    return {"correct": correct, "message": b["explanation"] if correct else message,
            "misplaced": misplaced, "broken": broken, "powered": powered}
