from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models.library import Chunk
from app.repos.keyword_store import SQLiteKeywordStore


def test_keyword_search_is_scoped_and_sanitizes_fts_syntax() -> None:
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        db.execute(text("CREATE VIRTUAL TABLE chunk_search USING fts5(chunk_id UNINDEXED, user_id UNINDEXED, document_id UNINDEXED, text)"))
        store = SQLiteKeywordStore(db)
        store.index_chunk(
            Chunk(id="a", user_id="alice", document_id="doc-a", text="binary search halves intervals", ordinal=0, page_start=1, page_end=1, token_count=4)
        )
        store.index_chunk(
            Chunk(id="b", user_id="bob", document_id="doc-b", text="binary search belongs to bob", ordinal=0, page_start=1, page_end=1, token_count=5)
        )
        db.commit()

        hits = store.search("alice", 'binary "search"', top_k=5)

        assert [hit.chunk_id for hit in hits] == ["a"]


def test_keyword_search_drops_question_stopwords_before_fts_matching() -> None:
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        db.execute(text("CREATE VIRTUAL TABLE chunk_search USING fts5(chunk_id UNINDEXED, user_id UNINDEXED, document_id UNINDEXED, text)"))
        store = SQLiteKeywordStore(db)
        store.index_chunk(
            Chunk(
                id="relevant",
                user_id="alice",
                document_id="doc-a",
                text="Neural sequence transduction models use an encoder and decoder.",
                ordinal=0,
                page_start=2,
                page_end=3,
                token_count=9,
            )
        )
        store.index_chunk(
            Chunk(
                id="distractor",
                user_id="alice",
                document_id="doc-a",
                text="The references discuss neural machine translation and sequence models.",
                ordinal=1,
                page_start=11,
                page_end=13,
                token_count=9,
            )
        )
        db.commit()

        hits = store.search("alice", "what is neural sequence", top_k=5)

        assert [hit.chunk_id for hit in hits[:2]] == ["relevant", "distractor"]
