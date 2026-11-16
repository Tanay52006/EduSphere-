from pydantic import BaseModel, ConfigDict


class SearchHitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    document_id: str
    text: str
    page_start: int
    page_end: int
    heading: str | None
    score: float
    sources: tuple[str, ...]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchHitResponse]


