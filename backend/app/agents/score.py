from collections import defaultdict
from typing import Any, Dict, List

from app.agents.schemas import ComplianceReport, Finding, FrameworkSummary
from app.agents.state import ComplianceState
from app.services import pipeline_log


SEVERITY_PENALTY = {"High": 12, "Medium": 6, "Low": 3}


def _summarize_frameworks(findings: List[Finding]) -> List[FrameworkSummary]:
    buckets: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"rules_evaluated": 0, "passed": 0, "warned": 0, "failed": 0}
    )
    for finding in findings:
        bucket = buckets[finding.framework]
        bucket["rules_evaluated"] += 1
        if finding.status == "pass":
            bucket["passed"] += 1
        elif finding.status == "warn":
            bucket["warned"] += 1
        elif finding.status == "fail":
            bucket["failed"] += 1

    return [FrameworkSummary(framework=name, **counts) for name, counts in buckets.items()]


def _label_for(score: int, has_findings: bool) -> str:
    if not has_findings:
        return "Inconclusive"
    if score >= 90:
        return "Compliant"
    if score >= 75:
        return "Mostly Compliant"
    if score >= 50:
        return "Needs Work"
    return "Non-Compliant"


def _summary_for(score: int, fail_count: int, warn_count: int, pass_count: int) -> str:
    if fail_count == 0 and warn_count == 0:
        return f"All {pass_count} evaluated rule(s) passed; document looks compliant."
    if fail_count == 0:
        return f"{pass_count} rule(s) passed and {warn_count} warning(s) flagged for review."
    return f"{fail_count} failure(s), {warn_count} warning(s), and {pass_count} pass(es) across the evaluated rules."


def score_node(state: ComplianceState) -> Dict[str, Any]:
    findings: List[Finding] = state.get("findings") or []
    pipeline_log.section("AGENT.SCORE")

    score = 100
    fail_count = warn_count = pass_count = 0
    for finding in findings:
        if finding.status == "fail":
            score -= SEVERITY_PENALTY.get(finding.severity, 6)
            fail_count += 1
        elif finding.status == "warn":
            score -= SEVERITY_PENALTY.get(finding.severity, 3) // 2
            warn_count += 1
        else:
            pass_count += 1

    score = max(0, min(100, score))
    label = _label_for(score, has_findings=bool(findings))
    summary = _summary_for(score, fail_count, warn_count, pass_count)
    framework_summaries = _summarize_frameworks(findings)

    report = ComplianceReport(
        score=score,
        label=label,
        summary=summary,
        frameworks=framework_summaries,
        findings=findings,
        llm_provider=state.get("llm_provider", "huggingface"),
        llm_model=state.get("llm_model", ""),
    )

    pipeline_log.kv(
        score=score,
        label=label,
        passed=pass_count,
        warned=warn_count,
        failed=fail_count,
    )

    return {"report": report}
