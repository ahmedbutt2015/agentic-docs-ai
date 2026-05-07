from typing import Any, Dict

from app.agents.rules import DEFAULT_FRAMEWORKS, rules_for_frameworks
from app.agents.state import ComplianceState
from app.services import pipeline_log


def retrieve_node(state: ComplianceState) -> Dict[str, Any]:
    active = state.get("active_frameworks") or DEFAULT_FRAMEWORKS
    rules = rules_for_frameworks(active)

    pipeline_log.section("AGENT.RETRIEVE", frameworks=",".join(active))
    pipeline_log.kv(
        rules_loaded=len(rules),
        gdpr=sum(1 for r in rules if r["framework"] == "GDPR"),
        soc2=sum(1 for r in rules if r["framework"] == "SOC2"),
        iso=sum(1 for r in rules if r["framework"] == "ISO27001"),
    )

    return {"applicable_rules": rules, "active_frameworks": list(active)}
