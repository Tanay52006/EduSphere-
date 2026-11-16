from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.ai.retrieval.hybrid import HybridRetriever
from app.models.library import Chunk
from app.repos.keyword_store import SQLiteKeywordStore
from app.repos.vector_store import SQLiteVectorStore


def test_hybrid_retriever_fuses_branches_and_returns_only_owned_chunks() -> None:
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        db.execute(
            text(
                "CREATE TABLE chunks (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, document_id TEXT NOT NULL, "
                "ordinal INTEGER NOT NULL, text TEXT NOT NULL, page_start INTEGER NOT NULL, page_end INTEGER NOT NULL, "
                "heading TEXT, token_count INTEGER NOT NULL)"
            )
        )
        db.execute(
            Chunk.__table__.insert(),
            [
                {
                    "id": "a", "user_id": "alice", "document_id": "doc-a", "ordinal": 0,
                    "text": "binary search", "page_start": 1, "page_end": 1, "token_count": 2,
                },
                {
                    "id": "b", "user_id": "alice", "document_id": "doc-b", "ordinal": 0,
                    "text": "vector search", "page_start": 2, "page_end": 2, "token_count": 2,
                },
                {
                    "id": "far", "user_id": "alice", "document_id": "doc-far", "ordinal": 0,
                    "text": "unrelated topic", "page_start": 3, "page_end": 3, "token_count": 2,
                },
                {
                    "id": "x", "user_id": "bob", "document_id": "doc-x", "ordinal": 0,
                    "text": "binary search", "page_start": 1, "page_end": 1, "token_count": 2,
                },
            ],
        )
        keyword = SQLiteKeywordStore(db)
        keyword.ensure_schema()
        for chunk in db.query(Chunk).all():
            keyword.index_chunk(chunk)
        vector = SQLiteVectorStore(db, dimensions=3)
        vector.add("doc-b", "alice", [1.0, 0.0, 0.0], {"chunk_id": "b"})
        vector.add("doc-far", "alice", [0.0, 0.0, 1.0], {"chunk_id": "far"})
        vector.add("doc-x", "bob", [1.0, 0.0, 0.0], {"chunk_id": "x"})
        db.commit()

        results = HybridRetriever(db, keyword, vector).search("alice", "binary", [1.0, 0.0, 0.0], top_k=5)

        assert {result.chunk_id for result in results} == {"a", "b"}
        assert set(results[0].sources) == {"keyword"}
        assert set(results[1].sources) == {"vector"}
