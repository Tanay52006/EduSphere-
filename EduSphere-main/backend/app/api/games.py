from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics import wrapper as analytics
from app.api.dependencies import get_current_user
from app.api.questions import owned_document
from app.core.db import get_db
from app.core.errors import AppError
from app.models.auth import User
from app.schemas.learning import AnswerQuestion, FlipCard, PauseClock, StartGame, SubmitGame
from app.services import games
from app.services.progress import award_game, summary

router = APIRouter(tags=["games"])


@router.get("/progress")
def progress(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    return summary(db, user)


@router.post("/games/sessions", status_code=201)
def start(payload: StartGame, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    owned_document(db, user.id, payload.document_id)
    games.lock_user(db, user)
    session = games.start_session(db, user, payload.document_id, payload.game)
    db.commit()
    analytics.track("Game Started", {"game": payload.game})
    return games.session_view(session)


@router.get("/games/sessions/{session_id}")
def resume(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    return games.session_view(games.owned_session(db, user, session_id, lock=False))


@router.post("/games/sessions/{session_id}/answer")
def answer(session_id: str, payload: AnswerQuestion, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    session = games.owned_session(db, user, session_id)
    games.answer(session, payload.question_id, payload.choice)
    db.commit()
    return games.session_view(session)


@router.post("/games/sessions/{session_id}/flip")
def flip(session_id: str, payload: FlipCard, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    session = games.owned_session(db, user, session_id)
    games.flip(session, payload.card_id)
    db.commit()
    return games.session_view(session)


@router.post("/games/sessions/{session_id}/next")
def next_question(session_id: str, payload: SubmitGame, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    session = games.owned_session(db, user, session_id)
    games.next_question(session)
    db.commit()
    return games.session_view(session)


@router.post("/games/sessions/{session_id}/clock")
def pause_clock(session_id: str, payload: PauseClock, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    session = games.owned_session(db, user, session_id)
    games.pause_clock(session, payload.paused)
    db.commit()
    return games.session_view(session)


@router.post("/games/sessions/{session_id}/submit")
def submit(session_id: str, payload: SubmitGame, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    session = games.owned_session(db, user, session_id)
    if session.result is not None:
        return session.result
    if session.status != "finished":
        raise AppError(409, "round_incomplete", "Finish the round before collecting your results.")
    state = session.state
    total, correct = len(state["questions"]), state["correct"]
    accuracy = correct / total if session.game == "quiz_blitz" else min(1.0, total / max(state["moves"], 1))
    duration = int((datetime.now(UTC) - session.started_at.replace(tzinfo=UTC)).total_seconds())
    xp = award_game(db, user, session, accuracy)
    session.status = "completed"
    db.flush()
    session.result = {"id": session.id, "game": session.game, "correct": correct, "total": total,
                      "accuracy": round(accuracy * 100), "moves": state["moves"], "duration_s": duration,
                      "score": state["score"], "xp_earned": xp, "review": state["history"], "progress": summary(db, user)}
    db.commit()
    analytics.track("Game Completed", {"game": session.game, "score": state["score"], "accuracy": accuracy,
                                      "duration_s": duration, "xp_earned": xp})
    return session.result


@router.post("/games/sessions/{session_id}/abandon", status_code=204)
def abandon(session_id: str, payload: SubmitGame, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:  # noqa: B008
    session = games.owned_session(db, user, session_id)
    if session.status == "open":
        session.status = "abandoned"
        db.commit()
        analytics.track("Game Abandoned", {"game": session.game})
