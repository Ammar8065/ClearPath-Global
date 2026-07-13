"""Drift guard: app/services/ai/field_catalog.py must mirror frontend/evaluation_config.js."""
from __future__ import annotations

import re
from pathlib import Path

from app.services.ai.field_catalog import ALLOWED_VALUES, FIELD_CATALOG, coerce_value

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_JS = ROOT_DIR / "frontend" / "evaluation_config.js"


def _js_source() -> str:
    return CONFIG_JS.read_text(encoding="utf-8")


def _default_state_keys(source: str) -> set[str]:
    match = re.search(r"export const DEFAULT_STATE = \{(.*?)\n\};", source, re.DOTALL)
    assert match, "DEFAULT_STATE block not found in evaluation_config.js"
    return set(re.findall(r"^\s*([a-z0-9_]+):", match.group(1), re.MULTILINE))


def _group_field_types(source: str) -> dict[str, str]:
    """Map each GROUPS field key to its declared type."""
    types: dict[str, str] = {}
    chunks = source.split('{ key: "')[1:]
    for chunk in chunks:
        key = chunk.split('"', 1)[0]
        type_match = re.search(r'type:\s*"(\w+)"', chunk)
        assert type_match, f"No type found for field {key!r} in evaluation_config.js"
        types[key] = type_match.group(1)
    return types


def test_catalog_keys_match_default_state():
    js_keys = _default_state_keys(_js_source())
    catalog_keys = set(FIELD_CATALOG)
    assert catalog_keys == js_keys, (
        f"Catalog drift — missing from Python: {sorted(js_keys - catalog_keys)}; "
        f"extra in Python: {sorted(catalog_keys - js_keys)}"
    )


def test_catalog_types_match_group_definitions():
    js_types = _group_field_types(_js_source())
    assert set(js_types) == set(FIELD_CATALOG)
    mismatches = {
        key: (spec.type, js_types[key])
        for key, spec in FIELD_CATALOG.items()
        if spec.type != js_types[key]
    }
    assert not mismatches, f"Type drift (python, js): {mismatches}"


def test_coerce_value_per_type():
    ternary = FIELD_CATALOG["australian_property_owned"]
    assert coerce_value(ternary, True) == (True, None)
    assert coerce_value(ternary, "yes")[1] is not None

    number = FIELD_CATALOG["days_in_country"]
    assert coerce_value(number, 183) == (183.0, None)
    assert coerce_value(number, 183.5) == (183.5, None)
    # bool is a subclass of int and must not pass as a number
    assert coerce_value(number, True)[1] is not None
    assert coerce_value(number, "183")[1] is not None
    assert coerce_value(number, float("inf"))[1] is not None

    jurisdiction = FIELD_CATALOG["citizenship"]
    assert coerce_value(jurisdiction, "US") == ("US", None)
    assert coerce_value(jurisdiction, "us") == ("US", None)
    assert coerce_value(jurisdiction, "FR")[1] is not None

    tax_status = FIELD_CATALOG["tax_residency_status"]
    assert coerce_value(tax_status, "Resident") == ("resident", None)
    assert coerce_value(tax_status, "citizen")[1] is not None

    us_state = FIELD_CATALOG["us_state_residency"]
    assert coerce_value(us_state, "ca") == ("CA", None)
    assert coerce_value(us_state, "TX")[1] is not None


def test_allowed_values_cover_enum_types():
    enum_types = {spec.type for spec in FIELD_CATALOG.values()} - {"ternary", "number"}
    assert enum_types == set(ALLOWED_VALUES)
