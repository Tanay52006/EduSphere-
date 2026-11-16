from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=8)


class ChatCitation(BaseModel):
    chunk_id: str
    document_id: str
    page_start: int
    page_end: int


class ChatResponse(BaseModel):
    answer: str
    citations: list[ChatCitation]
    grounded: bool


class GeneratedChat(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)
    citation_chunk_ids: list[str] = Field(max_length=8)
