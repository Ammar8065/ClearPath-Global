"""Report assembly — composes all engine sub-modules into a final result dict.

Entry point: ``run_evaluation(client, rules, client_data)``
    - ``rules`` must already be filtered to active + version-deduplicated
    - Returns a plain dict matching the ``EvaluationResponse`` schema shape
"""
from __future__ import annotations

from typing import Any

from app.engine.conditions import (
    evaluate_condition,
    missing_required_fields,
    parse_condition_expression,
)
from app.engine.interactions import find_interactions
from app.engine.scorer import (
    _normalize,
    category_breakdown,
    jurisdiction_breakdown,
    overall_risk,
    overall_score,
    rule_score,
)


def _source_url(source: Any) -> str:
    """Return a plain string URL regardless of whether it is an HttpUrl object."""
    url = getattr(source, "url", "") or ""
    return str(url)


def run_evaluation(
    client: Any,
    rules: list[Any],
    client_data: dict[str, Any],
    interactions: list[Any] = (),
) -> dict[str, Any]:
    """Core evaluation entry point — pure, no DB calls.

    Args:
        client:       Client ORM object (used for client_id).
        rules:        Active, version-deduplicated Rule ORM objects with
                      ``source`` relationship eagerly loaded.
        client_data:  Flat dict of client attributes sent in the request.
        interactions: Curated RuleInteraction rows (or dicts with the same
                      shape) to resolve against whichever rules end up
                      triggered. Optional — an empty/omitted list simply
                      means no interactions are reported, never an error.

    Returns:
        Plain dict matching EvaluationResponse schema.
    """
    triggered_rules: list[str] = []
    summary: list[dict[str, Any]] = []
    incomplete_rules: list[dict[str, Any]] = []
    warnings: list[str] = []

    for rule in rules:
        try:
            condition = parse_condition_expression(
                getattr(rule, "condition_expression", None)
            )
        except (ValueError, TypeError) as exc:
            warnings.append(
                f"Rule {getattr(rule, 'rule_code', '?')} skipped — "
                f"malformed condition: {exc}"
            )
            continue

        missing = missing_required_fields(condition, client_data)
        if missing:
            rl = _normalize(rule.risk_level)
            cat = _normalize(rule.category)
            incomplete_rules.append(
                {
                    "rule_code": getattr(rule, "rule_code", ""),
                    "description": getattr(rule, "description", ""),
                    "risk_level": rl,
                    "jurisdiction": getattr(rule, "jurisdiction", ""),
                    "category": cat,
                    "missing_fields": missing,
                    "reason": (
                        f"Cannot evaluate — missing: {', '.join(missing)}"
                    ),
                }
            )
            continue

        try:
            matched = evaluate_condition(condition, client_data)
        except (ValueError, TypeError, KeyError) as exc:
            warnings.append(
                f"Rule {getattr(rule, 'rule_code', '?')} skipped — "
                f"malformed condition: {exc}"
            )
            continue

        if not matched:
            continue

        source = getattr(rule, "source", None)
        source_title = getattr(source, "title", "") or ""
        source_url = _source_url(source)
        risk_lv = _normalize(rule.risk_level)
        conf_lv = _normalize(rule.confidence_level)
        cat = _normalize(rule.category)

        r_score = rule_score(risk_lv, conf_lv)
        rev_status = _normalize(getattr(rule, "review_status", "verified_current"))

        triggered_rules.append(rule.rule_code)
        summary.append(
            {
                "rule_code": rule.rule_code,
                "description": rule.description,
                "risk_level": risk_lv,
                "confidence_level": conf_lv,
                "jurisdiction": rule.jurisdiction,
                "category": cat,
                "rule_score": r_score,
                "source_id": rule.source_id,
                "source_title": source_title,
                "source_url": source_url,
                "section_reference": rule.section_reference,
                "review_status": rev_status,
            }
        )

    rule_interactions, interaction_warnings = find_interactions(set(triggered_rules), list(interactions))
    warnings.extend(interaction_warnings)

    cat_breakdown = category_breakdown(summary)
    jur_breakdown = jurisdiction_breakdown(summary)

    # Citations: one per unique (source_url, section_reference) pair.
    # Two rules from the same source but citing different sections are
    # distinct citations — critical for legal/tax traceability.
    seen_keys: set[tuple[str, str | None]] = set()
    citations: list[dict[str, Any]] = []
    for item in summary:
        key = (item["source_url"], item["section_reference"])
        if key not in seen_keys:
            seen_keys.add(key)
            citations.append(
                {
                    "rule_code": item["rule_code"],
                    "source_title": item["source_title"],
                    "source_url": item["source_url"],
                    "jurisdiction": item["jurisdiction"],
                    "section_reference": item["section_reference"],
                }
            )

    return {
        "client_id": getattr(client, "id", 0),
        "overall_risk": overall_risk(summary),
        "score": overall_score(cat_breakdown),
        "triggered_rules": triggered_rules,
        "summary": summary,
        "category_breakdown": cat_breakdown,
        "jurisdiction_breakdown": jur_breakdown,
        "citations": citations,
        "incomplete_rules": incomplete_rules,
        "rule_interactions": rule_interactions,
        "warnings": warnings,
    }
