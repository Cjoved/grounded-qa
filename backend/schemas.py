from typing import Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    status: str


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    chunk_text: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    chunks: int
    uploaded_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class EvalResult(BaseModel):
    question: str
    expected_source: Optional[str] = None
    retrieval_hit: bool
    faithfulness_score: float
    relevance_score: float


class EvalSummary(BaseModel):
    avg_retrieval_hit_rate: float
    avg_faithfulness: float
    avg_relevance: float


class EvalRunResponse(BaseModel):
    run_id: str
    results: list[EvalResult]
    summary: EvalSummary
