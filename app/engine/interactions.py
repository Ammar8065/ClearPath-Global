"""Rule interaction resolution — pure functions, no I/O, no DB.

A curated RuleInteraction row says "when both primary_rule_code and
related_rule_code fire together, related_rule_code changes what
primary_rule_code's finding means" (see app.models.rule_interaction and
seed_rule_interactions.py for the two interaction types and the rationale
behind each curated pair).

This module only asks: given the set of rule_codes that actually triggered
in this evaluation, which curated interactions apply? Every lookup is
defensive — a malformed or dangling interaction row degrades to a skipped
row plus a warning, exactly like a malformed rule condition does in
app.engine.report, rather than raising and failing the whole evaluation.
"""
from __future__ import annotations

from typing import Any


def _normalize(raw: Any) -> str:
    return str(getattr(raw, "value", raw)).lower()


def find_interactions(
    triggered_rule_codes: set[str],
    interactions: list[Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (found_interactions, warnings).

    ``interactions`` is the full curated set (typically every active
    RuleInteraction row) — filtering to the triggered set happens here, not
    at the caller, so this stays a single pure, testable seam.
    """
    found: list[dict[str, Any]] = []
    warnings: list[str] = []

    for item in interactions:
        try:
            primary = getattr(item, "primary_rule_code", None) or item["primary_rule_code"]
            related = getattr(item, "related_rule_code", None) or item["related_rule_code"]
            interaction_type = _normalize(
                getattr(item, "interaction_type", None)
                if hasattr(item, "interaction_type")
                else item["interaction_type"]
            )
            note = getattr(item, "note", None) if hasattr(item, "note") else item["note"]
        except (KeyError, TypeError) as exc:
            warnings.append(f"Rule interaction skipped — malformed record: {exc}")
            continue

        if not primary or not related or not note:
            warnings.append(
                f"Rule interaction skipped — missing field(s) on "
                f"{primary!r} -> {related!r}."
            )
            continue

        if primary == related:
            # A rule cannot modify its own finding; seed validation blocks this,
            # but rows written outside the seeder must not render a nonsense pair.
            warnings.append(
                f"Rule interaction skipped — {primary!r} references itself."
            )
            continue

        if primary not in triggered_rule_codes or related not in triggered_rule_codes:
            continue

        found.append(
            {
                "primary_rule_code": primary,
                "related_rule_code": related,
                "interaction_type": interaction_type,
                "note": note,
            }
        )

    return found, warnings
