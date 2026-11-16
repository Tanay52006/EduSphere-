import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.library import Chunk

_STOPWORDS = frozenset(
    {
        "a",
        "about",
        "an",
        "and",
        "are",
        "can",
        "could",
        "does",
        "do",
        "for",
        "from",
        "how",
        "in",
        "is",
        "me",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
        "you",
        "your",
    }
)


@dataclass(frozen=True)
class KeywordHit:
    chunk_id: str
    document_id: str
    score: float


class SQLiteKeywordStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_schema(self) -> None:
        self.db.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS chunk_search USING fts5("
                "chunk_id UNINDEXED, user_id UNINDEXED, document_id UNINDEXED, text)"
            )
        )

    def index_chunk(self, chunk: Chunk) -> None:
        self.db.execute(
            text("INSERT OR REPLACE INTO chunk_search (chunk_id, user_id, document_id, text) VALUES (:chunk_id, :user_id, :document_id, :text)"),
            {"chunk_id": chunk.id, "user_id": chunk.user_id, "document_id": chunk.document_id, "text": chunk.text},
        )

    def search(self, user_id: str, query: str, top_k: int = 5) -> list[KeywordHit]:
        tokens = [term for term in re.findall(r"[A-Za-z0-9_]+", query) if term.casefold() not in _STOPWORDS]
        if len(tokens) > 1:
            phrase = '"' + " ".join(tokens) + '"'
            terms = f"{phrase} OR {' '.join(tokens)}"
        else:
            terms = " ".join(tokens)
        if not terms:
            return []
        rows = self.db.execute(
            text(
                "SELECT chunk_id, document_id, bm25(chunk_search) AS score "
                "FROM chunk_search WHERE user_id = :user_id AND chunk_search MATCH :query "
                "ORDER BY score ASC, chunk_id ASC LIMIT :top_k"
            ),
            {"user_id": user_id, "query": terms, "top_k": top_k},
        )
        return [KeywordHit(str(row.chunk_id), str(row.document_id), float(row.score)) for row in rows]

    def delete_by_document(self, user_id: str, document_id: str) -> None:
        self.db.execute(
            text("DELETE FROM chunk_search WHERE user_id = :user_id AND document_id = :document_id"),
            {"user_id": user_id, "document_id": document_id},
        )
