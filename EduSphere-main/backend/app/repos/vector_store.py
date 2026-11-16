import json
import math
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class VectorItem:
    user_id: str
    document_id: str
    vector: list[float]
    metadata: dict[str, Any]


class VectorStore(Protocol):
    def add(self, document_id: str, user_id: str, vector: list[float], metadata: dict[str, Any]) -> None: ...
    def query(self, user_id: str, vector: list[float], top_k: int = 5, min_similarity: float | None = None) -> list[VectorItem]: ...
    def delete_by_document(self, user_id: str, document_id: str) -> None: ...


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._items: list[VectorItem] = []

    def add(self, document_id: str, user_id: str, vector: list[float], metadata: dict[str, Any]) -> None:
        self._items.append(VectorItem(user_id, document_id, vector, metadata))

    def query(self, user_id: str, vector: list[float], top_k: int = 5, min_similarity: float | None = None) -> list[VectorItem]:
        owned = [item for item in self._items if item.user_id == user_id]
        return sorted(owned, key=lambda item: self._distance(item.vector, vector))[:top_k]

    def delete_by_document(self, user_id: str, document_id: str) -> None:
        self._items = [item for item in self._items if not (item.user_id == user_id and item.document_id == document_id)]

    @staticmethod
    def _distance(first: list[float], second: list[float]) -> float:
        return math.sqrt(sum((left - right) ** 2 for left, right in zip(first, second, strict=True)))


class SQLiteVectorStore:
    """Persistent local vector storage for the SQLite development deployment.

    The table is deliberately hidden behind this repository boundary so a later
    PostgreSQL/pgvector implementation can preserve the same user-scoped API.
    """

    def __init__(self, db: Session, dimensions: int | None = None) -> None:
        if dimensions is not None and dimensions < 1:
            raise ValueError("dimensions must be positive")
        self._db = db
        self._dimensions = dimensions
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self._db.execute(
            text(
                "CREATE TABLE IF NOT EXISTS chunk_embeddings ("
                "chunk_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, document_id TEXT NOT NULL, "
                "vector_json TEXT NOT NULL, metadata_json TEXT NOT NULL"
                ")"
            )
        )
        self._db.execute(text("CREATE INDEX IF NOT EXISTS ix_chunk_embeddings_user_document ON chunk_embeddings (user_id, document_id)"))

    def add(self, document_id: str, user_id: str, vector: list[float], metadata: dict[str, Any]) -> None:
        chunk_id = metadata.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            raise ValueError("metadata.chunk_id is required")
        self._validate_vector(vector)
        self._db.execute(
            text(
                "INSERT INTO chunk_embeddings (chunk_id, user_id, document_id, vector_json, metadata_json) "
                "VALUES (:chunk_id, :user_id, :document_id, :vector_json, :metadata_json) "
                "ON CONFLICT(chunk_id) DO UPDATE SET user_id = excluded.user_id, document_id = excluded.document_id, "
                "vector_json = excluded.vector_json, metadata_json = excluded.metadata_json"
            ),
            {
                "chunk_id": chunk_id,
                "user_id": user_id,
                "document_id": document_id,
                "vector_json": json.dumps(vector, separators=(",", ":")),
                "metadata_json": json.dumps(metadata, separators=(",", ":")),
            },
        )

    def query(self, user_id: str, vector: list[float], top_k: int = 5, min_similarity: float | None = None) -> list[VectorItem]:
        self._validate_vector(vector)
        if top_k < 1:
            return []
        if min_similarity is not None and not 0 <= min_similarity <= 1:
            raise ValueError("min_similarity must be between 0 and 1")
        rows = self._db.execute(
            text(
                "SELECT user_id, document_id, vector_json, metadata_json "
                "FROM chunk_embeddings WHERE user_id = :user_id"
            ),
            {"user_id": user_id},
        ).mappings()
        scored: list[tuple[float, VectorItem]] = []
        for row in rows:
            stored = json.loads(row["vector_json"])
            if len(stored) != len(vector):
                continue
            item = VectorItem(row["user_id"], row["document_id"], stored, json.loads(row["metadata_json"]))
            distance = self._cosine_distance(item.vector, vector)
            if min_similarity is not None and 1.0 - distance < min_similarity:
                continue
            scored.append((distance, item))
        scored.sort(key=lambda result: (result[0], result[1].metadata.get("chunk_id", "")))
        return [item for _, item in scored[:top_k]]

    def delete_by_document(self, user_id: str, document_id: str) -> None:
        self._db.execute(
            text("DELETE FROM chunk_embeddings WHERE user_id = :user_id AND document_id = :document_id"),
            {"user_id": user_id, "document_id": document_id},
        )

    def _validate_vector(self, vector: list[float]) -> None:
        if not vector or (self._dimensions is not None and len(vector) != self._dimensions) or not all(math.isfinite(value) for value in vector):
            expected = f" exactly {self._dimensions}" if self._dimensions is not None else ""
            raise ValueError(f"vector must contain{expected} finite values")

    @staticmethod
    def _cosine_distance(first: list[float], second: list[float]) -> float:
        first_norm = math.sqrt(sum(value * value for value in first))
        second_norm = math.sqrt(sum(value * value for value in second))
        if first_norm == 0 or second_norm == 0:
            return 1.0
        similarity = sum(left * right for left, right in zip(first, second, strict=True)) / (first_norm * second_norm)
        return 1.0 - similarity
