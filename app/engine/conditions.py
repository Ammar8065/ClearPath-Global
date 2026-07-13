"""Condition evaluation — pure functions, no I/O, no DB.

Operator contracts
------------------
==, !=, >, >=, <, <=
    Standard numeric/string comparison.  TypeError returns False.

in
    • If actual is list/tuple/set: expected in actual
    • Else if expected is list/tuple/set: actual in expected
    • Otherwise (both scalars): plain equality — strings are deliberately
      NOT treated as containers, so "US" in "AUS" does not match.

not_in
    Negation of ``in``.

contains
    String-only, case-insensitive substring.
    ``actual`` must be a string; non-string actual returns False.

starts_with
    Case-insensitive prefix check.
    ``actual`` must be a string; non-string actual returns False.

is_empty
    True when actual is: None, "" , whitespace-only string, [], {}, (),
    or when the field is absent from client_data entirely — a fact that
    was never provided is empty. 0 and False are NOT empty.

not_empty
    Negation of ``is_empty``.
"""
from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any

_EMPTY_OPERATORS = {"is_empty", "not_empty"}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def _evaluate_membership(actual: Any, expected: Any, *, negate: bool = False) -> bool:
    if isinstance(actual, (list, tuple, set)):
        result = expected in actual
    elif isinstance(expected, (list, tuple, set)):
        result = actual in expected
    else:
        result = actual == expected
    return not result if negate else result


def _apply_operator(operator: str, actual: Any, expected: Any) -> bool:
    if operator == ">=":
        return actual >= expected
    if operator == "<=":
        return actual <= expected
    if operator == "==":
        return actual == expected
    if operator == "!=":
        return actual != expected
    if operator == ">":
        return actual > expected
    if operator == "<":
        return actual < expected
    if operator == "in":
        return _evaluate_membership(actual, expected)
    if operator == "not_in":
        return _evaluate_membership(actual, expected, negate=True)
    if operator == "contains":
        if not isinstance(actual, str):
            return False
        return str(expected).lower() in actual.lower()
    if operator == "starts_with":
        if not isinstance(actual, str):
            return False
        return actual.lower().startswith(str(expected).lower())
    if operator == "is_empty":
        return _is_empty(actual)
    if operator == "not_empty":
        return not _is_empty(actual)
    raise ValueError(f"Unsupported operator: {operator!r}")


def _evaluate_group(group_key: str, condition: dict[str, Any], client_data: dict[str, Any]) -> bool:
    items = condition.get(group_key)
    if not isinstance(items, list):
        raise ValueError(f"Condition group {group_key!r} must contain a list.")
    if not items:
        return False
    evaluator = all if group_key == "all" else any
    return evaluator(evaluate_condition(item, client_data) for item in items)


def _evaluate_leaf(condition: dict[str, Any], client_data: dict[str, Any]) -> bool:
    field = condition.get("field")
    operator = condition.get("operator")

    if field is None or operator is None:
        raise ValueError(f"Unrecognised condition format: {condition!r}")

    if operator not in _EMPTY_OPERATORS and "value" not in condition:
        raise ValueError(f"Unrecognised condition format: {condition!r}")

    if field not in client_data:
        # is_empty/not_empty are well-defined on missing data: a fact that
        # was never provided is empty. Every other operator cannot match.
        if operator in _EMPTY_OPERATORS:
            return _apply_operator(operator, None, None)
        return False

    actual_value = client_data[field]
    expected_value = None if operator in _EMPTY_OPERATORS else condition["value"]

    try:
        return _apply_operator(operator, actual_value, expected_value)
    except TypeError:
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_condition_expression(raw: Any) -> dict[str, Any]:
    """Normalise a rule's condition_expression to a plain dict."""
    if raw in (None, ""):
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except JSONDecodeError as exc:
            raise ValueError("Malformed condition_expression JSON.") from exc
        if not isinstance(parsed, dict):
            raise ValueError("condition_expression JSON must decode to an object.")
        return parsed
    raise ValueError("condition_expression must be a dict or JSON string.")


def evaluate_condition(condition: dict[str, Any], client_data: dict[str, Any]) -> bool:
    """Recursively evaluate a single or nested condition against flat client data."""
    if not condition:
        return False

    if "all" in condition:
        return _evaluate_group("all", condition, client_data)

    if "any" in condition:
        return _evaluate_group("any", condition, client_data)

    return _evaluate_leaf(condition, client_data)


def evaluate_rule(rule: Any, client_data: dict[str, Any]) -> bool:
    """Evaluate a Rule ORM object's condition_expression against client data."""
    condition = parse_condition_expression(getattr(rule, "condition_expression", None))
    return evaluate_condition(condition, client_data)


# ---------------------------------------------------------------------------
# Required-field collection (incomplete-data handling)
# ---------------------------------------------------------------------------

def collect_required_fields(condition: dict[str, Any]) -> list[str]:
    """Return the ordered, de-duplicated list of fields a condition *requires*.

    Fields referenced only by ``is_empty`` / ``not_empty`` are NOT required —
    those operators answer a well-defined question when the field is missing.

    Used to detect when a rule cannot be evaluated because the advisor
    has not yet provided the underlying fact (as opposed to the fact
    being "no"). Without this distinction, a missing answer would be
    silently treated as "condition not met", giving false certainty.
    """
    seen: list[str] = []

    def _walk(node: Any) -> None:
        if not isinstance(node, dict) or not node:
            return
        if "all" in node and isinstance(node["all"], list):
            for child in node["all"]:
                _walk(child)
            return
        if "any" in node and isinstance(node["any"], list):
            for child in node["any"]:
                _walk(child)
            return
        op = node.get("operator")
        field = node.get("field")
        if not isinstance(field, str) or not field:
            return
        if op in _EMPTY_OPERATORS:
            return
        if field not in seen:
            seen.append(field)

    _walk(condition)
    return seen


def missing_required_fields(condition: dict[str, Any], client_data: dict[str, Any]) -> list[str]:
    """Return the subset of required fields that are absent from the payload."""
    return [f for f in collect_required_fields(condition) if f not in client_data]
