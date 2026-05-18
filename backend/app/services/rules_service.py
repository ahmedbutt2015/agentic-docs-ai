from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.rules import RULES as DEFAULT_RULES
from app.database import SessionLocal
from app.models import ComplianceRule


def seed_default_rules_if_empty() -> int:
    db = SessionLocal()
    try:
        existing = db.scalar(select(func.count(ComplianceRule.id)))
        if existing:
            return 0

        for rule in DEFAULT_RULES:
            db.add(
                ComplianceRule(
                    rule_id=rule["rule_id"],
                    framework=rule["framework"],
                    title=rule["title"],
                    check=rule["check"],
                    severity=rule.get("severity", "Medium"),
                    is_default=True,
                    is_enabled=True,
                )
            )
        db.commit()
        return len(DEFAULT_RULES)
    finally:
        db.close()


def restore_missing_defaults(db: Session) -> List[ComplianceRule]:
    existing_ids = {row[0] for row in db.execute(select(ComplianceRule.rule_id)).all()}
    restored: List[ComplianceRule] = []
    for rule in DEFAULT_RULES:
        if rule["rule_id"] in existing_ids:
            continue
        instance = ComplianceRule(
            rule_id=rule["rule_id"],
            framework=rule["framework"],
            title=rule["title"],
            check=rule["check"],
            severity=rule.get("severity", "Medium"),
            is_default=True,
            is_enabled=True,
        )
        db.add(instance)
        restored.append(instance)
    db.commit()
    return restored


def list_rules(db: Session, framework: Optional[str] = None, enabled_only: bool = False) -> List[ComplianceRule]:
    stmt = select(ComplianceRule).order_by(ComplianceRule.framework, ComplianceRule.rule_id)
    if framework:
        stmt = stmt.where(ComplianceRule.framework == framework)
    if enabled_only:
        stmt = stmt.where(ComplianceRule.is_enabled.is_(True))
    return list(db.scalars(stmt).all())


def list_rules_for_frameworks(db: Session, frameworks: List[str]) -> List[Dict[str, Any]]:
    if not frameworks:
        return []
    stmt = select(ComplianceRule).where(
        ComplianceRule.is_enabled.is_(True),
        ComplianceRule.framework.in_(frameworks),
    )
    return [
        {
            "rule_id": rule.rule_id,
            "framework": rule.framework,
            "title": rule.title,
            "check": rule.check,
            "severity": rule.severity,
        }
        for rule in db.scalars(stmt).all()
    ]


def list_distinct_frameworks(db: Session) -> List[str]:
    rows = db.execute(
        select(ComplianceRule.framework).where(ComplianceRule.is_enabled.is_(True)).distinct().order_by(ComplianceRule.framework)
    ).all()
    return [row[0] for row in rows]


def get_rule(db: Session, rule_pk: int) -> Optional[ComplianceRule]:
    return db.get(ComplianceRule, rule_pk)


def _normalize_rule_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for key, value in payload.items():
        normalized[key] = value.strip() if isinstance(value, str) else value
    return normalized


def create_rule(db: Session, payload: Dict[str, Any]) -> ComplianceRule:
    normalized_payload = _normalize_rule_payload(payload)
    rule = ComplianceRule(
        rule_id=normalized_payload["rule_id"],
        framework=normalized_payload["framework"],
        title=normalized_payload["title"],
        check=normalized_payload["check"],
        severity=normalized_payload.get("severity", "Medium"),
        is_default=False,
        is_enabled=normalized_payload.get("is_enabled", True),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule: ComplianceRule, payload: Dict[str, Any]) -> ComplianceRule:
    payload = _normalize_rule_payload(payload)
    for field in ("rule_id", "framework", "title", "check", "severity"):
        if field in payload and payload[field] is not None:
            setattr(rule, field, payload[field])
    if "is_enabled" in payload and payload["is_enabled"] is not None:
        rule.is_enabled = bool(payload["is_enabled"])
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule: ComplianceRule) -> None:
    db.delete(rule)
    db.commit()
