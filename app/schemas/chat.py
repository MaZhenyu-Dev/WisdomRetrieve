from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)
    stream: bool = False


class ChatSource(BaseModel):
    document_id: int | None = None
    file: str
    page: int | None = None
    title: str | None = None
    chunk_index: int | None = None
    retrieval_sources: list[str] = Field(default_factory=list)
    vector_score: float | None = None
    bm25_score: float | None = None
    hybrid_score: float | None = None
    rerank_score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: str
    sources: list[ChatSource] = Field(default_factory=list)
    create_time: datetime


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
