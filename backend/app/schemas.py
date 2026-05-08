from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

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


class FindingResponse(BaseModel):
    rule_id: str
    framework: str
    status: str
    severity: str
    explanation: str
    evidence: Optional[str] = None


class FrameworkSummaryResponse(BaseModel):
    framework: str
    rules_evaluated: int
    passed: int
    warned: int
    failed: int


class ComplianceReportResponse(BaseModel):
    score: int
    label: str
    summary: str
    frameworks: List[FrameworkSummaryResponse] = Field(default_factory=list)
    findings: List[FindingResponse] = Field(default_factory=list)
    llm_provider: str
    llm_model: str


class ProcessingOptionResponse(BaseModel):
    key: str
    label: str
    enabled: bool


class ProcessingDetailsResponse(BaseModel):
    options: List[ProcessingOptionResponse] = Field(default_factory=list)
    selected_frameworks: List[str] = Field(default_factory=list)
    entity_count: int = 0
    chunks_indexed: int = 0
    compliance_status: Optional[str] = None


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
    compliance: Optional[ComplianceReportResponse] = None
    processing: Optional[ProcessingDetailsResponse] = None


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


class RuleBase(BaseModel):
    rule_id: str
    framework: str
    title: str
    check: str
    severity: str = "Medium"
    is_enabled: bool = True


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    rule_id: Optional[str] = None
    framework: Optional[str] = None
    title: Optional[str] = None
    check: Optional[str] = None
    severity: Optional[str] = None
    is_enabled: Optional[bool] = None


class RuleResponse(RuleBase):
    id: int
    is_default: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RuleRestoreResponse(BaseModel):
    restored: int
    rules: List[RuleResponse] = Field(default_factory=list)


class FrameworksResponse(BaseModel):
    frameworks: List[str] = Field(default_factory=list)


class JobSummaryResponse(BaseModel):
    id: str
    filename: str
    status: str
    created_at: datetime
    updated_at: datetime


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    job_id: Optional[str] = None
    history: List[ChatTurn] = Field(default_factory=list)
    limit: int = Field(6, ge=1, le=20)


class ChatCitationResponse(BaseModel):
    chunk_id: str
    job_id: str
    page_number: int
    chunk_index: int
    source_filename: Optional[str] = None
    preview: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: List[ChatCitationResponse] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    total_jobs: int
    completed_jobs: int
    processing_jobs: int
    pending_jobs: int
    failed_jobs: int
    total_issues: int
    average_score: int
    recent_jobs: List[RecentJobResponse] = Field(default_factory=list)
