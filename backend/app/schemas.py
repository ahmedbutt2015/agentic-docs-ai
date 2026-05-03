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
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    character_count: int
    word_count: int
    line_count: int
    page_count: Optional[int] = None


class ResultPayload(BaseModel):
    text: str
    entities: Dict[str, Any]
    metadata: MetadataResponse
    score: ScoreResponse
    issues: List[IssueResponse] = Field(default_factory=list)


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


class DashboardResponse(BaseModel):
    total_jobs: int
    completed_jobs: int
    processing_jobs: int
    pending_jobs: int
    failed_jobs: int
    total_issues: int
    average_score: int
    recent_jobs: List[RecentJobResponse] = Field(default_factory=list)
