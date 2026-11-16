from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session as DbSession

from app.ai.retrieval.hybrid import HybridRetriever
from app.api.dependencies import get_current_user
from app.core.db import get_db
from app.models.auth import User
from app.repos.keyword_store import SQLiteKeywordStore
from app.repos.vector_store import SQLiteVectorStore
from app.schemas.search import SearchHitResponse, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    request: Request,
    q: str = Query(min_length=1, max_length=500),  # noqa: B008
    top_k: int = Query(default=5, ge=1, le=20),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
    db: DbSession = Depends(get_db),  # noqa: B008
) -> SearchResponse:
    query_vector = await request.app.state.llm_provider.embed(q)
    retriever = HybridRetriever(db, SQLiteKeywordStore(db), SQLiteVectorStore(db))
    results = retriever.search(
        user.id,
        q,
        query_vector,
        top_k=top_k,
        min_vector_similarity=request.app.state.settings.retrieval_min_similarity,
    )
    return SearchResponse(
        query=q,
        results=[SearchHitResponse.model_validate(result) for result in results],
    )
