from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from pydantic import Field


class UploadResponse(BaseModel):
    id: str
    status: str
    filename: str


class StatusResponse(BaseModel):
    id: str
    status: str
    message: str
    filename: str
    created_at: datetime
    updated_at: datetime


class IssueResponse(BaseModel):
    severity: str
    severity_class: str
    rule: str
    description: str


class FrameworkStatusResponse(BaseModel):
    name: str
    status: str


class ScoreResponse(BaseModel):
    value: int
    label: str
    summary: str
    frameworks: List[FrameworkStatusResponse] = Field(default_factory=list)


class MetadataResponse(BaseModel):
    filename: str
    extension: str
    mime_type: str
    file_size_bytes: int
    file_size_label: str
    text_source: str
    parser_engine: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    character_count: int
    word_count: int
    line_count: int
    page_count: Optional[int] = None
    document_title: Optional[str] = None
    document_author: Optional[str] = None
    document_created_at: Optional[str] = None
    is_encrypted: bool = False


class WarningResponse(BaseModel):
    code: str
    message: str


class PageBlockResponse(BaseModel):
    text: str
    bbox: Optional[List[float]] = None
    confidence: float = 1.0


class PageResponse(BaseModel):
    page_number: int
    text: str
    sheet_name: Optional[str] = None
    blocks: List[PageBlockResponse] = Field(default_factory=list)


class ResultPayload(BaseModel):
    text: str
    entities: Dict[str, Any]
    metadata: MetadataResponse
    score: ScoreResponse
    issues: List[IssueResponse] = Field(default_factory=list)
    pages: List[PageResponse] = Field(default_factory=list)
    warnings: List[WarningResponse] = Field(default_factory=list)


class ResultResponse(BaseModel):
    id: str
    status: str
    message: str
    filename: str
    created_at: datetime
    updated_at: datetime
    result: Optional[ResultPayload] = None


class RecentJobResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str
    created_at: datetime
    updated_at: datetime
    score: Optional[int] = None
    issue_count: int = 0


class SearchHitResponse(BaseModel):
    chunk_id: str
    job_id: str
    page_number: int
    chunk_index: int
    text: str
    source_filename: Optional[str] = None
    score: float


class SearchResponse(BaseModel):
    query: str
    hits: List[SearchHitResponse] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    total_jobs: int
    completed_jobs: int
    processing_jobs: int
    pending_jobs: int
    failed_jobs: int
    total_issues: int
    average_score: int
    recent_jobs: List[RecentJobResponse] = Field(default_factory=list)
