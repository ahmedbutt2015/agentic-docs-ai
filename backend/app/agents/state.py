from typing import Any, Dict, List, Optional, TypedDict

from app.agents.schemas import ComplianceReport, Finding


class ComplianceState(TypedDict, total=False):
    job_id: str
    doc_filename: str
    doc_text: str
    active_frameworks: List[str]
    applicable_rules: List[Dict[str, Any]]
    findings: List[Finding]
    report: Optional[ComplianceReport]
    llm_provider: str
    llm_model: str
    errors: List[str]
