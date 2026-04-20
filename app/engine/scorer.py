"""Numeric scoring logic — pure functions, no I/O.

Rule score formula
------------------
    risk_weight:        low=1, medium=2, high=3
    confidence_weight:  low=0.6, medium=0.8, high=1.0
    rule_score = (risk_weight / 3) × confidence_weight × 100

Examples:
    high  + high   → 100.0
    high  + medium →  80.0
    medium + high  →  66.7
    low   + medium →  26.7

Category-level score
--------------------
    Average rule_score for triggered rules in that category.
    0.0 if no rules triggered.

Overall numeric score
---------------------
    Weighted average across the four categories:
        residency    30 %
        tax          30 %
        cross_border 25 %
        structure    15 %

Overall risk tier
-----------------
    ALWAYS determined by max(risk_level) — the numeric score is a second signal
    and never overrides severity.  This ensures a single high-confidence high-risk
    trigger cannot be diluted by many low-risk passes.
"""
from __future__ import annotations

from typing import Any

RISK_PRIORITY: dict[str, int] = {"low": 1, "medium": 2, "high": 3}

_RISK_WEIGHT: dict[str, float] = {"low": 1.0, "medium": 2.0, "high": 3.0}
_CONFIDENCE_WEIGHT: dict[str, float] = {"low": 0.6, "medium": 0.8, "high": 1.0}

_CATEGORY_WEIGHTS: dict[str, float] = {
    "residency": 0.30,
    "tax": 0.30,
    "cross_border": 0.25,
    "structure": 0.15,
}

ALL_CATEGORIES: tuple[str, ...] = tuple(_CATEGORY_WEIGHTS.keys())


def _normalize(raw: Any) -> str:
    """Return lowercase string value for an enum or plain string."""
    return str(getattr(raw, "value", raw)).lower()


def rule_score(risk_level: Any, confidence_level: Any) -> float:
    """Compute the individual rule contribution score (0-100)."""
    r = _normalize(risk_level)
    c = _normalize(confidence_level)
    if r not in _RISK_WEIGHT or c not in _CONFIDENCE_WEIGHT:
        return 0.0
    return round((_RISK_WEIGHT[r] / 3.0) * _CONFIDENCE_WEIGHT[c] * 100, 2)


def overall_risk(triggered_summaries: list[dict[str, Any]]) -> str:
    """Conservative max-severity determination."""
    if not triggered_summaries:
        return "low"
    return max(
        (item["risk_level"] for item in triggered_summaries),
        key=lambda lvl: RISK_PRIORITY.get(lvl, 0),
    )


def category_breakdown(triggered_summaries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per-category scores and counts."""
    buckets: dict[str, list[float]] = {cat: [] for cat in ALL_CATEGORIES}
    max_risk_per_cat: dict[str, str] = {cat: "low" for cat in ALL_CATEGORIES}

    for item in triggered_summaries:
        cat = item.get("category", "")
        if cat not in buckets:
            continue
        score = item.get("rule_score", 0.0)
        buckets[cat].append(score)
        rl = item.get("risk_level", "low")
        if RISK_PRIORITY.get(rl, 0) > RISK_PRIORITY.get(max_risk_per_cat[cat], 0):
            max_risk_per_cat[cat] = rl

    result: dict[str, dict[str, Any]] = {}
    for cat in ALL_CATEGORIES:
        scores = buckets[cat]
        result[cat] = {
            "score": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "triggered_count": len(scores),
            "max_risk": max_risk_per_cat[cat],
        }
    return result


def jurisdiction_breakdown(triggered_summaries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per-jurisdiction scores and counts."""
    buckets: dict[str, list[float]] = {}

    for item in triggered_summaries:
        j = item.get("jurisdiction", "")
        if j not in buckets:
            buckets[j] = []
        buckets[j].append(item.get("rule_score", 0.0))

    return {
        j: {
            "score": round(sum(scores) / len(scores), 2),
            "triggered_count": len(scores),
        }
        for j, scores in buckets.items()
    }


def overall_score(cat_breakdown: dict[str, dict[str, Any]]) -> float:
    """Weighted average across all four categories (0-100)."""
    total = sum(
        _CATEGORY_WEIGHTS.get(cat, 0.0) * data["score"]
        for cat, data in cat_breakdown.items()
    )
    return round(total, 2)
