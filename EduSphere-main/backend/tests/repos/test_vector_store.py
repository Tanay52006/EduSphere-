from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.repos.vector_store import SQLiteVectorStore


def test_sqlite_vector_store_persists_and_scopes_results() -> None:
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        store = SQLiteVectorStore(db, dimensions=3)
        store.add("doc-alice", "alice", [1.0, 0.0, 0.0], {"chunk_id": "alice-chunk"})
        store.add("doc-bob", "bob", [1.0, 0.0, 0.0], {"chunk_id": "bob-chunk"})
        db.commit()

        hits = store.query("alice", [1.0, 0.0, 0.0], top_k=5)

        assert [hit.document_id for hit in hits] == ["doc-alice"]
        assert hits[0].metadata == {"chunk_id": "alice-chunk"}


def test_sqlite_vector_store_orders_by_cosine_distance_and_deletes_owned_document() -> None:
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        store = SQLiteVectorStore(db, dimensions=3)
        store.add("doc-near", "alice", [0.9, 0.1, 0.0], {"chunk_id": "near"})
        store.add("doc-far", "alice", [0.0, 0.0, 1.0], {"chunk_id": "far"})
        store.add("doc-bob", "bob", [0.0, 0.0, 1.0], {"chunk_id": "bob"})
        db.commit()

        hits = store.query("alice", [1.0, 0.0, 0.0], top_k=2)
        store.delete_by_document("alice", "doc-near")
        db.commit()

        assert [hit.metadata["chunk_id"] for hit in hits] == ["near", "far"]
        assert [hit.document_id for hit in store.query("alice", [1.0, 0.0, 0.0])] == ["doc-far"]
        assert [hit.document_id for hit in store.query("bob", [0.0, 0.0, 1.0])] == ["doc-bob"]


def test_sqlite_vector_store_skips_embeddings_from_another_model_dimension() -> None:
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        store = SQLiteVectorStore(db)
        store.add("old-doc", "alice", [1.0, 0.0, 0.0], {"chunk_id": "old"})
        store.add("new-doc", "alice", [1.0, 0.0, 0.0, 0.0], {"chunk_id": "new"})
        db.commit()

        hits = store.query("alice", [1.0, 0.0, 0.0, 0.0])

        assert [hit.document_id for hit in hits] == ["new-doc"]


def test_sqlite_vector_store_skips_embeddings_below_similarity_threshold() -> None:
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        store = SQLiteVectorStore(db, dimensions=3)
        store.add("near-doc", "alice", [1.0, 0.0, 0.0], {"chunk_id": "near"})
        store.add("far-doc", "alice", [0.0, 0.0, 1.0], {"chunk_id": "far"})
        db.commit()

        hits = store.query("alice", [1.0, 0.0, 0.0], min_similarity=0.55)

        assert [hit.metadata["chunk_id"] for hit in hits] == ["near"]
