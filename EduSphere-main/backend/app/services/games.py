import hashlib
import random
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.auth import User
from app.models.learning import GameSession, Question

ROUND_SECONDS = 30


def lock_user(db: Session, user: User) -> None:
    # Serializes XP caps and session transitions on SQLite and Postgres.
    db.execute(update(User).where(User.id == user.id).values(id=user.id))


def owned_session(db: Session, user: User, session_id: str, *, lock: bool = True) -> GameSession:
    if lock:
        lock_user(db, user)
    session = db.scalar(select(GameSession).where(GameSession.id == session_id, GameSession.user_id == user.id))
    if session is None:
        raise AppError(404, "not_found", "Resource not found")
    return session


def open_session(session: GameSession, game: str) -> None:
    if session.status != "open" or session.game != game:
        raise AppError(409, "session_closed", "This round has ended. Start another session.")
    if (datetime.now(UTC) - session.started_at.replace(tzinfo=UTC)).total_seconds() > 3600:
        raise AppError(409, "session_expired", "This session has expired. Start a fresh round.")


def start_session(db: Session, user: User, document_id: str, game: str) -> GameSession:
    kind, minimum = ("MCQ", 10) if game == "quiz_blitz" else ("MATCH", 6)
    questions = list(db.scalars(select(Question).where(Question.user_id == user.id, Question.document_id == document_id,
                     Question.kind == kind, Question.validated.is_(True), Question.flagged.is_(False), Question.deleted.is_(False))))
    if len(questions) < minimum:
        raise AppError(409, "insufficient_questions", f"This game needs {minimum} validated {kind} questions. Generate a question bank first.")
    # The replay fingerprint ignores order while new rounds sample the whole bank.
    selected = random.SystemRandom().sample(questions, minimum)
    fingerprint = hashlib.sha256("|".join(sorted(q.id for q in selected)).encode()).hexdigest()
    random.SystemRandom().shuffle(selected)
    snapshots = [{"id": q.id, "prompt": q.prompt, **q.content} for q in selected]
    now = datetime.now(UTC)
    state: dict[str, Any] = {"questions": snapshots, "fingerprint": fingerprint, "index": 0, "correct": 0,
                            "lives": 3, "combo": 0, "score": 0, "history": [], "round_started": now.isoformat(),
                            "moves": 0, "revealed": [], "matched": [], "cards": [], "awaiting_next": False, "paused_at": None}
    if game == "memory_match":
        for q in snapshots:
            state["cards"].extend([{"id": str(uuid4()), "pair": q["id"], "text": q["term"]},
                                   {"id": str(uuid4()), "pair": q["id"], "text": q["definition"]}])
        random.SystemRandom().shuffle(state["cards"])
    session = GameSession(user_id=user.id, document_id=document_id, game=game, started_at=now, state=state)
    db.add(session)
    db.flush()
    return session


def session_view(session: GameSession) -> dict[str, Any]:
    state = session.state
    view: dict[str, Any] = {"id": session.id, "game": session.game, "status": session.status, "correct": state["correct"],
                           "total": len(state["questions"]), "index": state["index"], "lives": state["lives"],
                           "combo": state["combo"], "score": state["score"], "moves": state["moves"],
                           "started_at": session.started_at.isoformat(), "feedback": state.get("feedback"), "result": session.result}
    view["paused"] = state.get("paused_at") is not None
    if session.game == "quiz_blitz" and session.status == "open" and not state.get("awaiting_next"):
        q = state["questions"][state["index"]]
        view["question"] = {"id": q["id"], "prompt": q["prompt"], "options": q["options"]}
        view["deadline"] = datetime.fromisoformat(state["round_started"]).timestamp() + ROUND_SECONDS
    if session.game == "memory_match":
        visible = set(state["revealed"] + state["matched"])
        view["cards"] = [{"id": c["id"], "text": c["text"] if c["id"] in visible else None,
                          "matched": c["id"] in state["matched"]} for c in state["cards"]]
    return view


def answer(session: GameSession, question_id: str, choice: str) -> None:
    open_session(session, "quiz_blitz")
    state = dict(session.state)
    if state.get("awaiting_next") or state.get("paused_at"):
        raise AppError(409, "round_paused", "Continue the round before answering.")
    q = state["questions"][state["index"]]
    if q["id"] != question_id:
        raise AppError(409, "wrong_question", "This question has already been answered. Refresh the round.")
    timed_out = (datetime.now(UTC) - datetime.fromisoformat(state["round_started"])).total_seconds() > ROUND_SECONDS
    correct = choice == q["answer"] and not timed_out
    state["combo"] = state["combo"] + 1 if correct else 0
    state["correct"] += int(correct)
    state["lives"] -= int(not correct)
    state["score"] += (100 + 25 * min(state["combo"] - 1, 3)) if correct else 0
    feedback = {"correct": correct, "timed_out": timed_out, "answer": q["answer"], "explanation": q["explanation"], "sources": q["sources"]}
    state["history"] = state["history"] + [{"question_id": q["id"], "prompt": q["prompt"], **feedback}]
    state["feedback"] = feedback
    state["index"] += 1
    state["awaiting_next"] = True
    if state["index"] == len(state["questions"]) or state["lives"] == 0:
        session.status = "finished"
    session.state = state


def next_question(session: GameSession) -> None:
    open_session(session, "quiz_blitz")
    if not session.state.get("awaiting_next"):
        return
    session.state = {**session.state, "awaiting_next": False, "feedback": None, "paused_at": None, "round_started": datetime.now(UTC).isoformat()}


def pause_clock(session: GameSession, paused: bool) -> None:
    open_session(session, "quiz_blitz")
    state = dict(session.state)
    if state.get("awaiting_next"):
        return
    now = datetime.now(UTC)
    if paused and not state.get("paused_at"):
        state["paused_at"] = now.isoformat()
    elif not paused and state.get("paused_at"):
        gap = (now - datetime.fromisoformat(state["paused_at"])).total_seconds()
        state["round_started"] = (datetime.fromisoformat(state["round_started"]) + timedelta(seconds=gap)).isoformat()
        state["paused_at"] = None
    session.state = state


def flip(session: GameSession, card_id: str) -> None:
    open_session(session, "memory_match")
    state = dict(session.state)
    cards = {c["id"]: c for c in state["cards"]}
    if card_id not in cards or card_id in state["matched"]:
        raise AppError(422, "invalid_card", "Choose an unmatched card on this board.")
    revealed = [] if len(state["revealed"]) == 2 else list(state["revealed"])
    if card_id in revealed:
        raise AppError(409, "card_revealed", "Choose a different card.")
    revealed.append(card_id)
    state["revealed"] = revealed
    state["feedback"] = None
    if len(revealed) == 2:
        state["moves"] += 1
        match = cards[revealed[0]]["pair"] == cards[revealed[1]]["pair"]
        state["feedback"] = {"correct": match}
        if match:
            question = next(q for q in state["questions"] if q["id"] == cards[revealed[0]]["pair"])
            state["feedback"] = {"correct": True, "answer": question["definition"],
                                 "explanation": question["explanation"], "sources": question["sources"]}
            state["history"] = state["history"] + [{"question_id": question["id"], "prompt": question["prompt"], **state["feedback"]}]
            state["matched"] = state["matched"] + revealed
            state["revealed"] = []
            state["correct"] += 1
            if len(state["matched"]) == len(cards):
                session.status = "finished"
    session.state = state
