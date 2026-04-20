from datetime import date
from types import SimpleNamespace
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.engine import run_evaluation
from app.engine.conditions import evaluate_rule
from app.engine.selector import deduplicate_by_version
from app.models.client import Client
from app.models.rule import Rule


def _active_rules(db: Session) -> list[Rule]:
    today = date.today()
    rows = list(
        db.scalars(
            select(Rule)
            .options(joinedload(Rule.source))
            .where(
                Rule.is_deleted.is_(False),
                Rule.effective_from <= today,
                (Rule.effective_to.is_(None)) | (Rule.effective_to >= today),
            )
        )
    )
    return deduplicate_by_version(rows)


def _preview_rule_detail(rule: Rule, client_data: dict[str, Any]) -> tuple[bool, dict]:
    """Build a rule-match detail dict used by both preview flows.

    Returns (matched, detail_dict). Keeping as a module-private helper lets both
    preview_client and preview_private_assessment reuse the identical dict shape
    without either function being removed or altered at its public surface.
    """
    matched = evaluate_rule(rule, client_data)
    reason = (
        "All conditions satisfied."
        if matched
        else "One or more conditions not met, or required fields missing from payload."
    )

    cat = str(getattr(getattr(rule, "category", ""), "value", getattr(rule, "category", ""))).lower()
    rl = str(getattr(getattr(rule, "risk_level", "low"), "value", getattr(rule, "risk_level", "low"))).lower()

    detail = {
        "rule_code": rule.rule_code,
        "description": rule.description,
        "risk_level": rl,
        "jurisdiction": rule.jurisdiction,
        "category": cat,
        "version": rule.version,
        "matched": matched,
        "reason": reason,
    }
    return matched, detail


def evaluate_client(db: Session, client_id: int, client_data: dict[str, Any]) -> dict:
    client = db.get(Client, client_id)
    if client is None or client.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )

    rules = _active_rules(db)
    result = run_evaluation(client, rules, client_data)
    result["assessment_label"] = None
    return result


def evaluate_private_assessment(
    db: Session,
    client_data: dict[str, Any],
    *,
    assessment_label: str | None = None,
) -> dict:
    rules = _active_rules(db)
    result = run_evaluation(SimpleNamespace(id=None), rules, client_data)
    result["client_id"] = None
    result["assessment_label"] = assessment_label
    return result


def preview_client(db: Session, client_id: int, client_data: dict[str, Any]) -> dict:
    client = db.get(Client, client_id)
    if client is None or client.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )

    rules = _active_rules(db)
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
) -> dict:
    rules = _active_rules(db)
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
