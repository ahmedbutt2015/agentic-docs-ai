from typing import List, Literal, Optional

from pydantic import BaseModel, Field


SeverityLiteral = Literal["High", "Medium", "Low"]
StatusLiteral = Literal["pass", "warn", "fail"]
FrameworkLiteral = Literal["GDPR", "SOC2", "ISO27001"]


class Finding(BaseModel):
    rule_id: str
    framework: FrameworkLiteral
    status: StatusLiteral
    severity: SeverityLiteral
    explanation: str
    evidence: Optional[str] = None


class FindingsBatch(BaseModel):
    findings: List[Finding] = Field(default_factory=list)


class FrameworkSummary(BaseModel):
    framework: FrameworkLiteral
    rules_evaluated: int
    passed: int
    warned: int
    failed: int


class ComplianceReport(BaseModel):
    score: int
    label: str
    summary: str
    frameworks: List[FrameworkSummary] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)
    llm_provider: str
    llm_model: str
