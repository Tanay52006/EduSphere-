"""Deterministic retrieval evaluation over EduSphere's local PDF fixtures."""

import argparse
import json
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.ai.retrieval.hybrid import HybridRetriever
from app.models.library import Chunk
from app.repos.keyword_store import SQLiteKeywordStore
from app.repos.vector_store import SQLiteVectorStore
from app.services.ingestion import chunk_pages, extract_pages
from tools.fixture_spike import generate_fixture_set

USER_ID = "eval-user"
CASES: tuple[tuple[str, str, str], ...] = (
    ("How does cellular respiration make energy?", "lecture-notes.pdf", "cellular"),
    ("What is the time complexity of binary search?", "textbook-chapter.pdf", "binary"),
    ("How does photosynthesis make sugars?", "slides-export.pdf", "photosynthesis"),
    ("What is a dependent variable?", "exam-review.pdf", "experiment"),
)


class EvalReport(TypedDict):
    provider: str
    cases: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float


def _embedding(topic: str) -> list[float]:
    topics = {"cellular": [1.0, 0.0, 0.0, 0.0], "binary": [0.0, 1.0, 0.0, 0.0], "photosynthesis": [0.0, 0.0, 1.0, 0.0], "experiment": [0.0, 0.0, 0.0, 1.0]}
    return topics[topic]


def evaluate_fixture_set(output_dir: Path) -> EvalReport:
    fixture_dir = output_dir / "fixtures"
    generate_fixture_set(fixture_dir)
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        db.execute(
            text(
                "CREATE TABLE chunks (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, document_id TEXT NOT NULL, "
                "ordinal INTEGER NOT NULL, text TEXT NOT NULL, page_start INTEGER NOT NULL, page_end INTEGER NOT NULL, "
                "heading TEXT, token_count INTEGER NOT NULL)"
            )
        )
        keyword = SQLiteKeywordStore(db)
        keyword.ensure_schema()
        vector = SQLiteVectorStore(db, dimensions=4)
        document_ids: dict[str, str] = {}
        for _, filename, topic in CASES:
            document_id = str(uuid4())
            document_ids[filename] = document_id
            pages, _ = extract_pages((fixture_dir / filename).read_bytes())
            for item in chunk_pages(pages):
                chunk_id = str(uuid4())
                chunk = {
                    "id": chunk_id,
                    "user_id": USER_ID,
                    "document_id": document_id,
                    "ordinal": item.ordinal,
                    "text": item.text,
                    "page_start": item.page_start,
                    "page_end": item.page_end,
                    "heading": None,
                    "token_count": item.token_count,
                }
                db.execute(
                    text(
                        "INSERT INTO chunks (id, user_id, document_id, ordinal, text, page_start, page_end, heading, token_count) "
                        "VALUES (:id, :user_id, :document_id, :ordinal, :text, :page_start, :page_end, :heading, :token_count)"
                    ),
                    chunk,
                )
                keyword.index_chunk(Chunk(**chunk))
                vector.add(document_id, USER_ID, _embedding(topic), {"chunk_id": chunk_id})
        db.commit()

        retriever = HybridRetriever(db, keyword, vector)
        reciprocal_ranks: list[float] = []
        hits_1 = hits_3 = hits_5 = 0
        for question, filename, topic in CASES:
            hits = retriever.search(USER_ID, question, _embedding(topic), top_k=5)
            ranks = [index for index, hit in enumerate(hits, start=1) if hit.document_id == document_ids[filename]]
            if ranks:
                rank = ranks[0]
                reciprocal_ranks.append(1.0 / rank)
                hits_1 += rank <= 1
                hits_3 += rank <= 3
                hits_5 += rank <= 5
            else:
                reciprocal_ranks.append(0.0)
        total = len(CASES)
        return {
            "provider": "deterministic-offline",
            "cases": total,
            "hit_at_1": hits_1 / total,
            "hit_at_3": hits_3 / total,
            "hit_at_5": hits_5 / total,
            "mrr": sum(reciprocal_ranks) / total,
        }


def format_report(report: EvalReport) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/edusphere-rag-eval"))
    args = parser.parse_args()
    print(format_report(evaluate_fixture_set(args.output)), end="")


if __name__ == "__main__":
    main()
