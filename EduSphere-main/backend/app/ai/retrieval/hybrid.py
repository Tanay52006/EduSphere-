from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.retrieval.rrf import reciprocal_rank_fusion
from app.models.library import Chunk
from app.repos.keyword_store import SQLiteKeywordStore
from app.repos.vector_store import SQLiteVectorStore


@dataclass(frozen=True)
class HybridSearchHit:
    chunk_id: str
    document_id: str
    text: str
    page_start: int
    page_end: int
    heading: str | None
    score: float
    sources: tuple[str, ...]


class HybridRetriever:
    def __init__(self, db: Session, keyword_store: SQLiteKeywordStore, vector_store: SQLiteVectorStore) -> None:
        self._db = db
        self._keyword_store = keyword_store
        self._vector_store = vector_store

    def search(
        self,
        user_id: str,
        query: str,
        query_vector: list[float],
        top_k: int = 5,
        branch_k: int = 20,
        min_vector_similarity: float = 0.55,
    ) -> list[HybridSearchHit]:
        keyword_hits = self._keyword_store.search(user_id, query, top_k=branch_k)
        vector_hits = self._vector_store.query(user_id, query_vector, top_k=branch_k, min_similarity=min_vector_similarity)
        keyword_ids = [hit.chunk_id for hit in keyword_hits]
        vector_ids = [hit.metadata["chunk_id"] for hit in vector_hits if isinstance(hit.metadata.get("chunk_id"), str)]
        fused = reciprocal_rank_fusion([keyword_ids, vector_ids], top_k=top_k)
        if not fused:
            return []
        chunks = self._db.scalars(select(Chunk).where(Chunk.user_id == user_id, Chunk.id.in_([item.chunk_id for item in fused]))).all()
        by_id = {chunk.id: chunk for chunk in chunks}
        keyword_set = set(keyword_ids)
        vector_set = set(vector_ids)
        results: list[HybridSearchHit] = []
        for item in fused:
            chunk = by_id.get(item.chunk_id)
            if chunk is None:
                continue
            sources = tuple(source for source, ids in (("keyword", keyword_set), ("vector", vector_set)) if chunk.id in ids)
            results.append(HybridSearchHit(chunk.id, chunk.document_id, chunk.text, chunk.page_start, chunk.page_end, chunk.heading, item.score, sources))
        return results
