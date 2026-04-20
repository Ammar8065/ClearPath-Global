"""Rule selection — deduplication and active-version logic.

Layer 1 (creation-time): version overlap is enforced in ``app/services/rules.py``.
Layer 2 (selection-time): given a list of active rules, keep only the highest
    version for each rule_code.  This is the safeguard that ensures even if
    overlapping versions slip through they do not both fire.
"""
from __future__ import annotations

from typing import Any


def deduplicate_by_version(rules: list[Any]) -> list[Any]:
    """Return one rule per rule_code — the highest version number.

    Preserves original ordering for deterministic output.
    """
    latest: dict[str, Any] = {}
    for rule in rules:
        code = rule.rule_code
        if code not in latest or rule.version > latest[code].version:
            latest[code] = rule
    # preserve the original order among winners
    seen: set[str] = set()
    result: list[Any] = []
    for rule in rules:
        code = rule.rule_code
        if code not in seen and latest[code] is rule:
            seen.add(code)
            result.append(rule)
    return result
