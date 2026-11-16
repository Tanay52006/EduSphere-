"""Reconcile both Phase 3 histories without discarding existing learning data."""
import json
from datetime import UTC, date, datetime
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from alembic import op

revision = "0009_reconcile_phase3"
down_revision = ("0008_learning_activities", "0007_gamification")
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    metadata = sa.MetaData()

    def table(name):
        return sa.Table(name, metadata, autoload_with=bind)

    def rows(name):
        return bind.execute(sa.select(table(name))).mappings().all() if inspector.has_table(name) else []

    questions = table("questions")
    chunks = {c["id"]: c for c in rows("chunks")}
    profiles = {p["user_id"]: p for p in rows("profiles")}
    previous_questions = {q["id"]: q for q in rows("legacy_questions")}
    for old in previous_questions.values():
        payload, answer = json.loads(old["payload_json"]), json.loads(old["answer_json"])
        ids = json.loads(old["source_chunk_ids_json"])
        cited = [chunks[i] for i in ids if i in chunks and chunks[i]["user_id"] == old["user_id"]
                 and chunks[i]["document_id"] == old["document_id"]]
        sources = [{"chunk_id": c["id"], "page_start": c["page_start"], "page_end": c["page_end"],
                    "url": f"/api/documents/{old['document_id']}/file#page={c['page_start']}"} for c in cited]
        content = {"options": payload.get("options", []), "answer": str(answer.get("value", "")),
                   "explanation": old["explanation"], "difficulty": {"easy": 1, "medium": 2, "hard": 3}.get(old["difficulty"], 1),
                   "term": None, "definition": None, "sources": sources, "legacy_question_id": old["id"],
                   "source_chunk_id": cited[0]["id"] if cited else "", "source_quote": cited[0]["text"][:600] if cited else ""}
        records = []
        if old["type"] == "MATCH":
            for index, pair in enumerate(payload.get("pairs", [])):
                if not isinstance(pair, dict) or not pair.get("term") or not pair.get("definition"):
                    continue
                pair_id = old["id"] if index == 0 else str(uuid5(NAMESPACE_URL, f"edusphere:{old['id']}:{index}"))
                records.append({"id": pair_id, "kind": "MATCH",
                    "prompt": f"Match the concept: {pair['term']}",
                    "content": {**content, "options": [], "answer": pair["definition"], "term": pair["term"], "definition": pair["definition"]}})
        elif old["type"] in {"MCQ", "TF"}:
            if old["type"] == "TF":
                content.update(options=["True", "False"], answer="True" if answer.get("value") is True else "False")
            records.append({"id": old["id"], "kind": "MCQ", "prompt": old["prompt"], "content": content})
        for record in records:
            data = record["content"]
            shape_ok = bool(data["term"] and data["definition"]) if record["kind"] == "MATCH" else (
                isinstance(data["options"], list) and 2 <= len(data["options"]) <= 4
                and all(isinstance(option, str) and option.strip() for option in data["options"])
                and len(set(data["options"])) == len(data["options"]) and data["answer"] in data["options"])
            bind.execute(questions.insert().values(**record, user_id=old["user_id"], document_id=old["document_id"],
                         validated=bool(old["validated"] and cited and len(cited) == len(set(ids)) and shape_ok), flagged=False, deleted=False))

    for old in rows("legacy_xp_events"):
        when = old["created_at"].replace(tzinfo=UTC)
        timezone = profiles.get(old["user_id"], {}).get("timezone", "UTC")
        bind.execute(table("xp_events").insert().values(id=old["id"], user_id=old["user_id"], source=old["source"], ref=old["id"],
                     amount=old["amount"], created_at=old["created_at"], local_day=str(when.astimezone(ZoneInfo(timezone)).date())))
    for old in rows("legacy_streaks"):
        bind.execute(table("streaks").insert().values(user_id=old["user_id"], last_day=str(old["last_activity_date"]) if old["last_activity_date"] else None,
                     current=old["current_streak"], longest=old["longest_streak"], freeze_week=None))
    badges = {b["id"]: b["code"] for b in rows("legacy_badges")}
    for old in rows("legacy_user_badges"):
        code = badges.get(old["badge_id"], old["badge_id"])
        bind.execute(table("user_badges").insert().values(user_id=old["user_id"], key=code[:32], earned_at=old["earned_at"]))

    def progress(user_id):
        today = datetime.now(UTC).astimezone(ZoneInfo(profiles.get(user_id, {}).get("timezone", "UTC"))).date()
        events = [e for e in rows("xp_events") if e["user_id"] == user_id]
        total = sum(e["amount"] for e in events)
        daily = sum(e["amount"] for e in events if e["local_day"] == str(today))
        into, level = total, 1
        while into >= 100 + 50 * level:
            into -= 100 + 50 * level
            level += 1
        streak = next((s for s in rows("streaks") if s["user_id"] == user_id), {})
        current = streak.get("current", 0) if streak.get("last_day") and (today - date.fromisoformat(streak["last_day"])).days <= 1 else 0
        return {"total_xp": total, "today_xp": daily, "level": level, "level_xp": into, "level_target": 100 + 50 * level,
                "tier": ["Curious", "Explorer", "Scholar", "Sage"][min((level - 1) // 5, 3)], "streak": current,
                "longest_streak": streak.get("longest", 0), "daily_goal": 20, "daily_goal_met": daily >= 20,
                "activities": sum(s["user_id"] == user_id and s["status"] == "completed" for s in rows("legacy_game_sessions")), "badges": []}

    results = {r["session_id"]: r for r in rows("legacy_game_results")}
    for old in rows("legacy_game_sessions"):
        previous = results.get(old["id"])
        if previous and previous["user_id"] != old["user_id"]:
            previous = None
        history = []
        for review in json.loads(previous["answers_json"]) if previous else []:
            question = previous_questions.get(review.get("question_id"), {})
            expected = review.get("correct_answer", {})
            review_sources = [{"chunk_id": c["id"], "page_start": c["page_start"], "page_end": c["page_end"],
                               "url": f"/api/documents/{c['document_id']}/file#page={c['page_start']}"}
                              for c in chunks.values() if c["id"] in review.get("source_chunk_ids", []) and c["user_id"] == old["user_id"]]
            history.append({"question_id": review.get("question_id", ""), "prompt": question.get("prompt", "Previous study session"),
                            "correct": bool(review.get("correct")), "answer": str(expected.get("value", expected)),
                            "explanation": review.get("explanation", ""), "sources": review_sources})
        total, correct = (previous["total_count"], previous["correct_count"]) if previous else (len(json.loads(old["question_ids_json"])), 0)
        result = None
        if previous:
            result = {"id": old["id"], "game": old["game_type"], "correct": correct, "total": total, "accuracy": round(100 * correct / max(1, total)),
                      "moves": 0, "duration_s": 0, "score": previous["score"], "xp_earned": previous["xp_earned"], "review": history,
                      "progress": progress(old["user_id"])}
        state = {"questions": json.loads(old["question_ids_json"]), "fingerprint": f"legacy:{old['id']}", "index": total, "correct": correct,
                 "lives": 0, "combo": 0, "score": previous["score"] if previous else 0, "moves": 0,
                 "history": history, "revealed": [], "matched": [], "cards": [], "awaiting_next": True, "paused_at": None}
        bind.execute(table("game_sessions").insert().values(id=old["id"], user_id=old["user_id"], document_id=old["document_id"],
                     game=old["game_type"], status="completed" if previous else "abandoned", started_at=old["started_at"] or datetime.now(UTC),
                     state=state, result=result))


def downgrade() -> None:
    raise RuntimeError("Restore a pre-upgrade backup to reverse the Phase 3 reconciliation without losing learning history.")
