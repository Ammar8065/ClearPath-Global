from datetime import date
from types import SimpleNamespace
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.engine import run_evaluation
from app.engine.conditions import evaluate_rule, missing_required_fields, parse_condition_expression
from app.engine.scorer import _normalize
from app.engine.selector import deduplicate_by_version
from app.models.client import Client
from app.models.rule import Rule
from app.models.rule_interaction import RuleInteraction


def _active_rules(db: Session, jurisdiction_scope: list[str] | None = None) -> list[Rule]:
    """Active, version-deduplicated rules — optionally limited to a set of
    jurisdiction codes.

    Scoping exists because generic worksheet fields (days_in_country,
    tax_residency_status, ...) describe "the relevant country": without a
    scope, one payload value would be read as a different country's fact by
    each jurisdiction's rules. An empty/None scope evaluates everything.
    """
    today = date.today()
    statement = (
        select(Rule)
        .options(joinedload(Rule.source))
        .where(
            Rule.is_deleted.is_(False),
            Rule.effective_from <= today,
            (Rule.effective_to.is_(None)) | (Rule.effective_to >= today),
        )
    )
    if jurisdiction_scope:
        statement = statement.where(Rule.jurisdiction.in_(jurisdiction_scope))
    rows = list(db.scalars(statement))
    return deduplicate_by_version(rows)


def _active_interactions(db: Session) -> list[RuleInteraction]:
    return list(db.scalars(select(RuleInteraction)))


def _preview_rule_detail(rule: Rule, client_data: dict[str, Any]) -> tuple[bool, dict]:
    """Build a rule-match detail dict used by both preview flows.

    Returns (matched, detail_dict). Distinguishes between "condition evaluated
    to false" and "required fields missing" so the preview doesn't silently
    claim a rule doesn't match when it simply can't be evaluated.
    """
    cat = _normalize(rule.category)
    rl = _normalize(rule.risk_level)
    rev = _normalize(getattr(rule, "review_status", "verified_current"))

    try:
        condition = parse_condition_expression(getattr(rule, "condition_expression", None))
    except (ValueError, TypeError):
        return False, {
            "rule_code": rule.rule_code, "description": rule.description,
            "risk_level": rl, "jurisdiction": rule.jurisdiction, "category": cat,
            "version": rule.version, "matched": False,
            "reason": "Malformed condition — rule skipped.",
            "review_status": rev,
        }

    missing = missing_required_fields(condition, client_data)
    if missing:
        return False, {
            "rule_code": rule.rule_code, "description": rule.description,
            "risk_level": rl, "jurisdiction": rule.jurisdiction, "category": cat,
            "version": rule.version, "matched": False,
            "reason": f"Cannot evaluate — missing: {', '.join(missing)}",
            "review_status": rev,
        }

    matched = evaluate_rule(rule, client_data)
    reason = "All conditions satisfied." if matched else "Conditions not met."

    return matched, {
        "rule_code": rule.rule_code, "description": rule.description,
        "risk_level": rl, "jurisdiction": rule.jurisdiction, "category": cat,
        "version": rule.version, "matched": matched, "reason": reason,
        "review_status": rev,
    }


def _require_active_client(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None or client.is_deleted:
        raise LookupError("Client not found.")
    return client


def evaluate_client(
    db: Session,
    client_id: int,
    client_data: dict[str, Any],
    *,
    assessment_label: str | None = None,
    jurisdiction_scope: list[str] | None = None,
) -> dict:
    client = _require_active_client(db, client_id)

    rules = _active_rules(db, jurisdiction_scope)
    interactions = _active_interactions(db)
    result = run_evaluation(client, rules, client_data, interactions)
    result["assessment_label"] = assessment_label
    return result


def evaluate_private_assessment(
    db: Session,
    client_data: dict[str, Any],
    *,
    assessment_label: str | None = None,
    jurisdiction_scope: list[str] | None = None,
) -> dict:
    rules = _active_rules(db, jurisdiction_scope)
    interactions = _active_interactions(db)
    result = run_evaluation(SimpleNamespace(id=None), rules, client_data, interactions)
    result["client_id"] = None
    result["assessment_label"] = assessment_label
    return result


def preview_client(
    db: Session,
    client_id: int,
    client_data: dict[str, Any],
    *,
    jurisdiction_scope: list[str] | None = None,
) -> dict:
    _require_active_client(db, client_id)

    rules = _active_rules(db, jurisdiction_scope)
    rule_details = []
    matched_count = 0

    for rule in rules:
        matched, detail = _preview_rule_detail(rule, client_data)
        if matched:
            matched_count += 1
        rule_details.append(detail)

    return {
        "client_id": client_id,
        "assessment_label": None,
        "total_active_rules": len(rules),
        "matched_count": matched_count,
        "rules": rule_details,
    }


def preview_private_assessment(
    db: Session,
    client_data: dict[str, Any],
    *,
    assessment_label: str | None = None,
    jurisdiction_scope: list[str] | None = None,
) -> dict:
    rules = _active_rules(db, jurisdiction_scope)
    rule_details = []
    matched_count = 0

    for rule in rules:
        matched, detail = _preview_rule_detail(rule, client_data)
        if matched:
            matched_count += 1
        rule_details.append(detail)

    return {
        "client_id": None,
        "assessment_label": assessment_label,
        "total_active_rules": len(rules),
        "matched_count": matched_count,
        "rules": rule_details,
    }
