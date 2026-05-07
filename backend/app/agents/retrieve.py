from collections import Counter
from typing import Any, Dict

from app.agents.state import ComplianceState
from app.database import SessionLocal
from app.services import pipeline_log
from app.services.rules_service import list_distinct_frameworks, list_rules_for_frameworks


def retrieve_node(state: ComplianceState) -> Dict[str, Any]:
    requested = state.get("active_frameworks") or []

    db = SessionLocal()
    try:
        active = list(requested) if requested else list_distinct_frameworks(db)
        rules = list_rules_for_frameworks(db, active) if active else []
    finally:
        db.close()

    by_framework = Counter(rule["framework"] for rule in rules)

    pipeline_log.section("AGENT.RETRIEVE", frameworks=",".join(active) if active else "(none)")
    pipeline_log.kv(
        rules_loaded=len(rules),
        per_framework=", ".join(f"{name}:{count}" for name, count in sorted(by_framework.items())) or "none",
    )

    return {"applicable_rules": rules, "active_frameworks": list(active)}
