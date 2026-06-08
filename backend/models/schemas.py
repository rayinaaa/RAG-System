from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    id: str
    filename: str
    path: str
    status: Literal["queued", "processing", "ready", "failed"]
    progress: int = 0
    chunk_count: int = 0
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None = None
    section_title: str | None = None


class TextChunk(BaseModel):
    text: str
    metadata: ChunkMetadata


class RetrievedChunk(BaseModel):
    text: str
    metadata: ChunkMetadata
    vector_score: float = 0
    keyword_score: float = 0
    final_score: float = 0
    rerank_score: float | None = None
    citation_number: int | None = None


class SourceCitation(BaseModel):
    number: int
    filename: str
    page_number: int | None = None
    section_title: str | None = None
    chunk_id: str
    preview: str | None = None
    confidence: float = 0


class QueryUnderstanding(BaseModel):
    query_type: Literal["search", "summary", "comparison", "follow_up"]
    expanded_queries: list[str] = Field(default_factory=list)
    rationale: str


class RetrievedEvidence(BaseModel):
    citation_number: int
    filename: str
    page_number: int | None = None
    section_title: str | None = None
    chunk_id: str
    text: str
    vector_score: float
    keyword_score: float
    final_score: float
    rerank_score: float | None = None


class AnswerExplanation(BaseModel):
    query_understanding: QueryUnderstanding
    retrieved_chunks: list[RetrievedEvidence]
    context: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default_factory=lambda: str(uuid4()))


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceCitation]
    retrieval_ms: float
    generation_ms: float
    confidence: float = 0
    confidence_label: Literal["high", "medium", "low"] = "low"
    explanation: AnswerExplanation | None = None


class DocumentSummaryResponse(BaseModel):
    document_id: str
    filename: str
    summary: str
    suggested_questions: list[str]
    key_topics: list[str] = Field(default_factory=list)
    important_dates: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    detail: str
