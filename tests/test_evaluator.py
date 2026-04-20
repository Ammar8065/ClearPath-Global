"""Tests for the M2 rules engine (app/engine/) and schema validation.

Covers:
  - app/engine/conditions.py   — all operators, nested groups, edge cases
  - app/engine/scorer.py       — rule_score, overall_risk, breakdowns
  - app/engine/selector.py     — version deduplication
  - app/engine/report.py       — run_evaluation end-to-end, citations, warnings
  - app/schemas/rule.py        — write-time condition_expression validation
"""
from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from app.engine.conditions import (
    collect_required_fields,
    evaluate_condition,
    evaluate_rule,
    missing_required_fields,
    parse_condition_expression,
)
from app.engine.scorer import (
    ALL_CATEGORIES,
    category_breakdown,
    jurisdiction_breakdown,
    overall_risk,
    overall_score,
    rule_score,
)
from app.engine.selector import deduplicate_by_version
from app.engine.report import run_evaluation
from app.models.rule import ConfidenceLevel, RiskLevel, Rule, RuleCategory
from app.schemas.rule import RuleCreate, _validate_condition_node


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def make_rule(
    *,
    condition_expression,
    rule_code: str = "TEST_RULE",
    risk_level=RiskLevel.low,
    confidence_level=ConfidenceLevel.high,
    category=RuleCategory.residency,
    jurisdiction: str = "AU",
    is_deleted: bool = False,
    version: int = 1,
    source_id: int = 1,
    section_reference: str | None = None,
):
    return Rule(
        rule_code=rule_code,
        jurisdiction=jurisdiction,
        category=category,
        condition_expression=condition_expression,
        description=f"Test rule {rule_code}",
        risk_level=risk_level,
        confidence_level=confidence_level,
        version=version,
        effective_from=date(2025, 1, 1),
        effective_to=None,
        is_deleted=is_deleted,
        source_id=source_id,
        section_reference=section_reference,
    )


def make_source(source_id: int = 1, title: str = "Test Source", url: str = "https://example.com/source"):
    return SimpleNamespace(id=source_id, title=title, url=url)


def make_rule_with_source(*, source=None, **kwargs):
    """Create a plain namespace rule with source attached for report tests.

    Uses SimpleNamespace instead of the ORM Rule to avoid SQLAlchemy
    relationship management (which rejects non-ORM source objects).
    run_evaluation accesses everything via getattr, so this works.
    """
    defaults = {
        "rule_code": kwargs.get("rule_code", "TEST_RULE"),
        "jurisdiction": kwargs.get("jurisdiction", "AU"),
        "category": kwargs.get("category", RuleCategory.residency),
        "condition_expression": kwargs.get("condition_expression"),
        "description": f"Test rule {kwargs.get('rule_code', 'TEST_RULE')}",
        "risk_level": kwargs.get("risk_level", RiskLevel.low),
        "confidence_level": kwargs.get("confidence_level", ConfidenceLevel.high),
        "version": kwargs.get("version", 1),
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": kwargs.get("is_deleted", False),
        "source_id": kwargs.get("source_id", 1),
        "section_reference": kwargs.get("section_reference"),
        "source": source or make_source(source_id=kwargs.get("source_id", 1)),
    }
    return SimpleNamespace(**defaults)


# ═══════════════════════════════════════════════════════════════════════════
# conditions.py — parse_condition_expression
# ═══════════════════════════════════════════════════════════════════════════

class TestParseConditionExpression:
    def test_dict_passthrough(self):
        d = {"field": "x", "operator": "==", "value": 1}
        assert parse_condition_expression(d) is d

    def test_json_string(self):
        assert parse_condition_expression('{"field":"x","operator":"==","value":1}') == {
            "field": "x", "operator": "==", "value": 1,
        }

    def test_none_returns_empty(self):
        assert parse_condition_expression(None) == {}

    def test_empty_string_returns_empty(self):
        assert parse_condition_expression("") == {}

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Malformed"):
            parse_condition_expression("{bad json")

    def test_json_array_raises(self):
        with pytest.raises(ValueError, match="object"):
            parse_condition_expression("[1,2,3]")

    def test_non_string_non_dict_raises(self):
        with pytest.raises(ValueError, match="dict or JSON string"):
            parse_condition_expression(42)


# ═══════════════════════════════════════════════════════════════════════════
# conditions.py — evaluate_condition (all operators)
# ═══════════════════════════════════════════════════════════════════════════

class TestEvaluateConditionOperators:
    """Every supported operator gets explicit coverage."""

    def test_gte_true(self):
        assert evaluate_condition({"field": "x", "operator": ">=", "value": 10}, {"x": 10}) is True

    def test_gte_false(self):
        assert evaluate_condition({"field": "x", "operator": ">=", "value": 10}, {"x": 9}) is False

    def test_lte_true(self):
        assert evaluate_condition({"field": "x", "operator": "<=", "value": 10}, {"x": 10}) is True

    def test_lte_false(self):
        assert evaluate_condition({"field": "x", "operator": "<=", "value": 10}, {"x": 11}) is False

    def test_eq_true(self):
        assert evaluate_condition({"field": "x", "operator": "==", "value": "AU"}, {"x": "AU"}) is True

    def test_eq_false(self):
        assert evaluate_condition({"field": "x", "operator": "==", "value": "AU"}, {"x": "SG"}) is False

    def test_neq_true(self):
        assert evaluate_condition({"field": "x", "operator": "!=", "value": "AU"}, {"x": "SG"}) is True

    def test_neq_false(self):
        assert evaluate_condition({"field": "x", "operator": "!=", "value": "AU"}, {"x": "AU"}) is False

    def test_gt_true(self):
        assert evaluate_condition({"field": "x", "operator": ">", "value": 5}, {"x": 6}) is True

    def test_gt_boundary(self):
        assert evaluate_condition({"field": "x", "operator": ">", "value": 5}, {"x": 5}) is False

    def test_lt_true(self):
        assert evaluate_condition({"field": "x", "operator": "<", "value": 5}, {"x": 4}) is True

    def test_lt_boundary(self):
        assert evaluate_condition({"field": "x", "operator": "<", "value": 5}, {"x": 5}) is False

    def test_in_value_in_list(self):
        """actual is a list, expected is a scalar."""
        assert evaluate_condition(
            {"field": "citizenships", "operator": "in", "value": "US"},
            {"citizenships": ["US", "AU"]},
        ) is True

    def test_in_actual_in_expected_list(self):
        """actual is scalar, expected is a list."""
        assert evaluate_condition(
            {"field": "country", "operator": "in", "value": ["US", "AU"]},
            {"country": "AU"},
        ) is True

    def test_in_false(self):
        assert evaluate_condition(
            {"field": "country", "operator": "in", "value": ["US", "AU"]},
            {"country": "SG"},
        ) is False

    def test_not_in_true(self):
        assert evaluate_condition(
            {"field": "country", "operator": "not_in", "value": ["US", "AU"]},
            {"country": "SG"},
        ) is True

    def test_not_in_false(self):
        assert evaluate_condition(
            {"field": "country", "operator": "not_in", "value": ["US", "AU"]},
            {"country": "US"},
        ) is False

    def test_contains_true(self):
        assert evaluate_condition(
            {"field": "notes", "operator": "contains", "value": "expat"},
            {"notes": "Australian Expatriate"},
        ) is True

    def test_contains_false(self):
        assert evaluate_condition(
            {"field": "notes", "operator": "contains", "value": "resident"},
            {"notes": "tourist"},
        ) is False

    def test_contains_non_string_actual_returns_false(self):
        assert evaluate_condition(
            {"field": "x", "operator": "contains", "value": "a"},
            {"x": 123},
        ) is False

    def test_starts_with_true(self):
        assert evaluate_condition(
            {"field": "code", "operator": "starts_with", "value": "AU_"},
            {"code": "AU_RES_001"},
        ) is True

    def test_starts_with_false(self):
        assert evaluate_condition(
            {"field": "code", "operator": "starts_with", "value": "SG_"},
            {"code": "AU_RES_001"},
        ) is False

    def test_is_empty_none(self):
        assert evaluate_condition(
            {"field": "x", "operator": "is_empty", "value": None},
            {"x": None},
        ) is True

    def test_is_empty_blank_string(self):
        assert evaluate_condition(
            {"field": "x", "operator": "is_empty", "value": None},
            {"x": "  "},
        ) is True

    def test_is_empty_empty_list(self):
        assert evaluate_condition(
            {"field": "x", "operator": "is_empty", "value": None},
            {"x": []},
        ) is True

    def test_is_empty_zero_is_not_empty(self):
        assert evaluate_condition(
            {"field": "x", "operator": "is_empty", "value": None},
            {"x": 0},
        ) is False

    def test_not_empty_true(self):
        assert evaluate_condition(
            {"field": "x", "operator": "not_empty", "value": None},
            {"x": "hello"},
        ) is True

    def test_not_empty_false(self):
        assert evaluate_condition(
            {"field": "x", "operator": "not_empty", "value": None},
            {"x": ""},
        ) is False

    def test_unsupported_operator_raises(self):
        with pytest.raises(ValueError, match="Unsupported operator"):
            evaluate_condition({"field": "x", "operator": "~=", "value": 1}, {"x": 1})


# ═══════════════════════════════════════════════════════════════════════════
# conditions.py — nested groups and edge cases
# ═══════════════════════════════════════════════════════════════════════════

class TestEvaluateConditionGroups:
    def test_all_group_true(self):
        cond = {"all": [
            {"field": "a", "operator": "==", "value": 1},
            {"field": "b", "operator": "==", "value": 2},
        ]}
        assert evaluate_condition(cond, {"a": 1, "b": 2}) is True

    def test_all_group_false_when_one_fails(self):
        cond = {"all": [
            {"field": "a", "operator": "==", "value": 1},
            {"field": "b", "operator": "==", "value": 2},
        ]}
        assert evaluate_condition(cond, {"a": 1, "b": 999}) is False

    def test_any_group_true_with_one_match(self):
        cond = {"any": [
            {"field": "a", "operator": "==", "value": 1},
            {"field": "b", "operator": "==", "value": 2},
        ]}
        assert evaluate_condition(cond, {"a": 999, "b": 2}) is True

    def test_any_group_false_when_none_match(self):
        cond = {"any": [
            {"field": "a", "operator": "==", "value": 1},
            {"field": "b", "operator": "==", "value": 2},
        ]}
        assert evaluate_condition(cond, {"a": 999, "b": 999}) is False

    def test_deeply_nested_groups(self):
        cond = {"all": [
            {"any": [
                {"field": "x", "operator": "==", "value": 1},
                {"field": "y", "operator": "==", "value": 2},
            ]},
            {"field": "z", "operator": ">", "value": 0},
        ]}
        assert evaluate_condition(cond, {"x": 999, "y": 2, "z": 5}) is True
        assert evaluate_condition(cond, {"x": 999, "y": 999, "z": 5}) is False

    def test_empty_condition_returns_false(self):
        assert evaluate_condition({}, {"x": 1}) is False

    def test_missing_field_returns_false(self):
        cond = {"field": "missing_key", "operator": ">=", "value": 10}
        assert evaluate_condition(cond, {"other_key": 100}) is False

    def test_type_mismatch_returns_false(self):
        """Comparing string to int should not raise — returns False."""
        cond = {"field": "x", "operator": ">=", "value": 10}
        assert evaluate_condition(cond, {"x": "not_a_number"}) is False

    def test_malformed_leaf_raises(self):
        with pytest.raises(ValueError, match="Unrecognised condition format"):
            evaluate_condition({"field": "x"}, {"x": 1})

    def test_group_with_non_list_raises(self):
        with pytest.raises(ValueError, match="must contain a list"):
            evaluate_condition({"all": "not a list"}, {"x": 1})

    def test_empty_group_returns_false(self):
        assert evaluate_condition({"any": []}, {"x": 1}) is False


# ═══════════════════════════════════════════════════════════════════════════
# conditions.py — evaluate_rule (ORM integration)
# ═══════════════════════════════════════════════════════════════════════════

class TestEvaluateRule:
    def test_dict_condition(self):
        rule = make_rule(condition_expression={"field": "x", "operator": ">=", "value": 5})
        assert evaluate_rule(rule, {"x": 10}) is True

    def test_json_string_condition(self):
        rule = make_rule(
            condition_expression='{"field": "x", "operator": ">=", "value": 5}'
        )
        assert evaluate_rule(rule, {"x": 10}) is True

    def test_none_condition_returns_false(self):
        rule = make_rule(condition_expression=None)
        assert evaluate_rule(rule, {"x": 10}) is False


# ═══════════════════════════════════════════════════════════════════════════
# scorer.py
# ═══════════════════════════════════════════════════════════════════════════

class TestRuleScore:
    def test_high_high(self):
        assert rule_score("high", "high") == 100.0

    def test_high_medium(self):
        assert rule_score("high", "medium") == 80.0

    def test_medium_high(self):
        assert rule_score("medium", "high") == 66.67

    def test_low_medium(self):
        assert rule_score("low", "medium") == 26.67

    def test_low_low(self):
        assert rule_score("low", "low") == 20.0

    def test_unknown_risk_returns_zero(self):
        assert rule_score("unknown", "high") == 0.0

    def test_enum_values(self):
        """Works with enum objects, not just strings."""
        assert rule_score(RiskLevel.high, ConfidenceLevel.high) == 100.0


class TestOverallRisk:
    def test_no_triggers_returns_low(self):
        assert overall_risk([]) == "low"

    def test_single_high(self):
        assert overall_risk([{"risk_level": "high"}]) == "high"

    def test_mixed_returns_highest(self):
        items = [{"risk_level": "low"}, {"risk_level": "medium"}, {"risk_level": "high"}]
        assert overall_risk(items) == "high"

    def test_all_low(self):
        items = [{"risk_level": "low"}, {"risk_level": "low"}]
        assert overall_risk(items) == "low"


class TestCategoryBreakdown:
    def test_empty_input(self):
        result = category_breakdown([])
        for cat in ALL_CATEGORIES:
            assert result[cat]["score"] == 0.0
            assert result[cat]["triggered_count"] == 0
            assert result[cat]["max_risk"] == "low"

    def test_single_category(self):
        items = [{"category": "tax", "rule_score": 80.0, "risk_level": "high"}]
        result = category_breakdown(items)
        assert result["tax"]["score"] == 80.0
        assert result["tax"]["triggered_count"] == 1
        assert result["tax"]["max_risk"] == "high"
        assert result["residency"]["triggered_count"] == 0

    def test_multiple_rules_same_category(self):
        items = [
            {"category": "residency", "rule_score": 100.0, "risk_level": "high"},
            {"category": "residency", "rule_score": 20.0, "risk_level": "low"},
        ]
        result = category_breakdown(items)
        assert result["residency"]["score"] == 60.0
        assert result["residency"]["triggered_count"] == 2
        assert result["residency"]["max_risk"] == "high"

    def test_unknown_category_ignored(self):
        items = [{"category": "unknown_cat", "rule_score": 50.0, "risk_level": "medium"}]
        result = category_breakdown(items)
        for cat in ALL_CATEGORIES:
            assert result[cat]["triggered_count"] == 0


class TestJurisdictionBreakdown:
    def test_empty(self):
        assert jurisdiction_breakdown([]) == {}

    def test_single_jurisdiction(self):
        items = [{"jurisdiction": "AU", "rule_score": 80.0}]
        result = jurisdiction_breakdown(items)
        assert result["AU"]["score"] == 80.0
        assert result["AU"]["triggered_count"] == 1

    def test_multiple_jurisdictions(self):
        items = [
            {"jurisdiction": "AU", "rule_score": 100.0},
            {"jurisdiction": "AU", "rule_score": 60.0},
            {"jurisdiction": "SG", "rule_score": 40.0},
        ]
        result = jurisdiction_breakdown(items)
        assert result["AU"]["score"] == 80.0
        assert result["AU"]["triggered_count"] == 2
        assert result["SG"]["score"] == 40.0


class TestOverallScore:
    def test_zero_when_nothing_triggered(self):
        cat_bd = {cat: {"score": 0.0, "triggered_count": 0, "max_risk": "low"} for cat in ALL_CATEGORIES}
        assert overall_score(cat_bd) == 0.0

    def test_weighted_average(self):
        cat_bd = {
            "residency": {"score": 100.0},
            "tax": {"score": 100.0},
            "cross_border": {"score": 100.0},
            "structure": {"score": 100.0},
        }
        # 0.30*100 + 0.30*100 + 0.25*100 + 0.15*100 = 100
        assert overall_score(cat_bd) == 100.0


# ═══════════════════════════════════════════════════════════════════════════
# selector.py
# ═══════════════════════════════════════════════════════════════════════════

class TestDeduplicateByVersion:
    def test_keeps_highest_version(self):
        r1 = SimpleNamespace(rule_code="A", version=1)
        r2 = SimpleNamespace(rule_code="A", version=2)
        r3 = SimpleNamespace(rule_code="A", version=3)
        result = deduplicate_by_version([r1, r2, r3])
        assert len(result) == 1
        assert result[0].version == 3

    def test_different_codes_kept(self):
        r1 = SimpleNamespace(rule_code="A", version=1)
        r2 = SimpleNamespace(rule_code="B", version=1)
        result = deduplicate_by_version([r1, r2])
        assert len(result) == 2

    def test_preserves_order(self):
        r1 = SimpleNamespace(rule_code="B", version=2)
        r2 = SimpleNamespace(rule_code="A", version=1)
        r3 = SimpleNamespace(rule_code="B", version=1)
        result = deduplicate_by_version([r1, r2, r3])
        assert [r.rule_code for r in result] == ["B", "A"]

    def test_empty_input(self):
        assert deduplicate_by_version([]) == []

    def test_single_rule(self):
        r = SimpleNamespace(rule_code="X", version=1)
        assert deduplicate_by_version([r]) == [r]


# ═══════════════════════════════════════════════════════════════════════════
# report.py — run_evaluation
# ═══════════════════════════════════════════════════════════════════════════

class TestRunEvaluation:
    def test_basic_trigger(self):
        client = SimpleNamespace(id=1)
        rule = make_rule_with_source(
            rule_code="R1",
            condition_expression={"field": "x", "operator": ">=", "value": 10},
            risk_level=RiskLevel.high,
            confidence_level=ConfidenceLevel.high,
        )
        result = run_evaluation(client, [rule], {"x": 20})
        assert result["client_id"] == 1
        assert result["overall_risk"] == "high"
        assert result["triggered_rules"] == ["R1"]
        assert len(result["summary"]) == 1
        assert result["summary"][0]["rule_code"] == "R1"
        assert result["warnings"] == []

    def test_no_triggers(self):
        client = SimpleNamespace(id=1)
        rule = make_rule_with_source(
            condition_expression={"field": "x", "operator": ">=", "value": 999},
        )
        result = run_evaluation(client, [rule], {"x": 1})
        assert result["triggered_rules"] == []
        assert result["overall_risk"] == "low"
        assert result["score"] == 0.0

    def test_multiple_rules_mixed(self):
        client = SimpleNamespace(id=1)
        rules = [
            make_rule_with_source(
                rule_code="LOW",
                condition_expression={"field": "a", "operator": "==", "value": 1},
                risk_level=RiskLevel.low,
            ),
            make_rule_with_source(
                rule_code="HIGH",
                condition_expression={"field": "b", "operator": "==", "value": 2},
                risk_level=RiskLevel.high,
            ),
            make_rule_with_source(
                rule_code="MISS",
                condition_expression={"field": "c", "operator": "==", "value": 3},
                risk_level=RiskLevel.medium,
            ),
        ]
        result = run_evaluation(client, rules, {"a": 1, "b": 2, "c": 999})
        assert set(result["triggered_rules"]) == {"LOW", "HIGH"}
        assert result["overall_risk"] == "high"

    def test_malformed_rule_skipped_with_warning(self):
        """A rule with an invalid condition should be skipped, not crash."""
        client = SimpleNamespace(id=1)
        good_rule = make_rule_with_source(
            rule_code="GOOD",
            condition_expression={"field": "x", "operator": ">=", "value": 1},
            risk_level=RiskLevel.low,
        )
        bad_rule = make_rule_with_source(
            rule_code="BAD",
            condition_expression={"field": "x"},  # missing operator and value
        )
        result = run_evaluation(client, [good_rule, bad_rule], {"x": 5})
        assert result["triggered_rules"] == ["GOOD"]
        assert len(result["warnings"]) == 1
        assert "BAD" in result["warnings"][0]

    def test_citation_dedup_by_url_and_section(self):
        """Same source URL but different section_reference = separate citations."""
        client = SimpleNamespace(id=1)
        source = make_source(url="https://legislation.gov.au/itaa1997")
        rules = [
            make_rule_with_source(
                rule_code="R1",
                condition_expression={"field": "x", "operator": "==", "value": 1},
                risk_level=RiskLevel.high,
                section_reference="s6-5(1)",
                source=source,
            ),
            make_rule_with_source(
                rule_code="R2",
                condition_expression={"field": "y", "operator": "==", "value": 2},
                risk_level=RiskLevel.medium,
                section_reference="s995-1",
                source=source,
            ),
        ]
        result = run_evaluation(client, rules, {"x": 1, "y": 2})
        assert len(result["citations"]) == 2
        sections = {c["section_reference"] for c in result["citations"]}
        assert sections == {"s6-5(1)", "s995-1"}

    def test_citation_dedup_same_url_same_section(self):
        """Same source URL and same section_reference = single citation."""
        client = SimpleNamespace(id=1)
        source = make_source(url="https://legislation.gov.au/itaa1997")
        rules = [
            make_rule_with_source(
                rule_code="R1",
                condition_expression={"field": "x", "operator": "==", "value": 1},
                risk_level=RiskLevel.high,
                section_reference="s6-5(1)",
                source=source,
            ),
            make_rule_with_source(
                rule_code="R2",
                condition_expression={"field": "y", "operator": "==", "value": 2},
                risk_level=RiskLevel.medium,
                section_reference="s6-5(1)",
                source=source,
            ),
        ]
        result = run_evaluation(client, rules, {"x": 1, "y": 2})
        assert len(result["citations"]) == 1

    def test_result_has_category_and_jurisdiction_breakdowns(self):
        client = SimpleNamespace(id=1)
        rule = make_rule_with_source(
            rule_code="R1",
            condition_expression={"field": "x", "operator": "==", "value": 1},
            risk_level=RiskLevel.high,
            category=RuleCategory.tax,
            jurisdiction="SG",
        )
        result = run_evaluation(client, [rule], {"x": 1})
        assert "tax" in result["category_breakdown"]
        assert result["category_breakdown"]["tax"]["triggered_count"] == 1
        assert "SG" in result["jurisdiction_breakdown"]
        assert result["jurisdiction_breakdown"]["SG"]["triggered_count"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# conditions.py — required-field collection (incomplete-data handling)
# ═══════════════════════════════════════════════════════════════════════════

class TestCollectRequiredFields:
    def test_leaf_comparison_requires_field(self):
        cond = {"field": "days_in_country", "operator": ">", "value": 183}
        assert collect_required_fields(cond) == ["days_in_country"]

    def test_is_empty_does_not_require_field(self):
        cond = {"field": "notes", "operator": "is_empty"}
        assert collect_required_fields(cond) == []

    def test_not_empty_does_not_require_field(self):
        cond = {"field": "notes", "operator": "not_empty"}
        assert collect_required_fields(cond) == []

    def test_nested_all_collects_all_fields(self):
        cond = {"all": [
            {"field": "a", "operator": "==", "value": 1},
            {"field": "b", "operator": ">", "value": 2},
        ]}
        assert collect_required_fields(cond) == ["a", "b"]

    def test_nested_any_with_deep_tree(self):
        cond = {"any": [
            {"all": [
                {"field": "citizenship", "operator": "==", "value": "US"},
                {"field": "foreign_income", "operator": ">", "value": 100000},
            ]},
            {"field": "tax_residency_status", "operator": "==", "value": "resident"},
        ]}
        assert collect_required_fields(cond) == [
            "citizenship", "foreign_income", "tax_residency_status",
        ]

    def test_duplicate_fields_deduplicated(self):
        cond = {"any": [
            {"field": "x", "operator": "==", "value": 1},
            {"field": "x", "operator": ">", "value": 5},
        ]}
        assert collect_required_fields(cond) == ["x"]

    def test_empty_condition_returns_empty_list(self):
        assert collect_required_fields({}) == []


class TestMissingRequiredFields:
    def test_all_present(self):
        cond = {"field": "x", "operator": "==", "value": 1}
        assert missing_required_fields(cond, {"x": 1}) == []

    def test_single_missing(self):
        cond = {"field": "x", "operator": "==", "value": 1}
        assert missing_required_fields(cond, {}) == ["x"]

    def test_partial_missing_in_group(self):
        cond = {"all": [
            {"field": "a", "operator": "==", "value": 1},
            {"field": "b", "operator": "==", "value": 2},
        ]}
        assert missing_required_fields(cond, {"a": 1}) == ["b"]

    def test_is_empty_field_not_required(self):
        """Rule should still be evaluable when is_empty references a missing field."""
        cond = {"field": "notes", "operator": "is_empty"}
        assert missing_required_fields(cond, {}) == []


class TestRunEvaluationIncomplete:
    """When required facts are missing, the rule must land in `incomplete_rules`
    rather than silently evaluating to False — that's what gives advisors the
    confidence to trust the score."""

    def test_missing_field_produces_incomplete_entry(self):
        client = SimpleNamespace(id=1)
        rule = make_rule_with_source(
            rule_code="RES_183",
            condition_expression={"field": "days_in_country", "operator": ">", "value": 183},
            risk_level=RiskLevel.high,
        )
        result = run_evaluation(client, [rule], {})
        assert result["triggered_rules"] == []
        assert len(result["incomplete_rules"]) == 1
        entry = result["incomplete_rules"][0]
        assert entry["rule_code"] == "RES_183"
        assert entry["missing_fields"] == ["days_in_country"]
        assert "days_in_country" in entry["reason"]

    def test_incomplete_rule_does_not_trigger_or_score(self):
        """An incomplete rule must not contribute to the overall score."""
        client = SimpleNamespace(id=1)
        rule = make_rule_with_source(
            rule_code="RES_183",
            condition_expression={"field": "days_in_country", "operator": ">", "value": 183},
            risk_level=RiskLevel.high,
            confidence_level=ConfidenceLevel.high,
        )
        result = run_evaluation(client, [rule], {})
        assert result["score"] == 0.0
        assert result["overall_risk"] == "low"

    def test_partial_data_splits_triggered_and_incomplete(self):
        client = SimpleNamespace(id=1)
        complete_rule = make_rule_with_source(
            rule_code="HAVE_DATA",
            condition_expression={"field": "a", "operator": "==", "value": 1},
            risk_level=RiskLevel.low,
        )
        incomplete_rule = make_rule_with_source(
            rule_code="NEED_DATA",
            condition_expression={"field": "b", "operator": "==", "value": 2},
            risk_level=RiskLevel.high,
        )
        result = run_evaluation(client, [complete_rule, incomplete_rule], {"a": 1})
        assert result["triggered_rules"] == ["HAVE_DATA"]
        assert [r["rule_code"] for r in result["incomplete_rules"]] == ["NEED_DATA"]

    def test_incomplete_multi_field_lists_all_missing(self):
        client = SimpleNamespace(id=1)
        rule = make_rule_with_source(
            rule_code="MULTI",
            condition_expression={"all": [
                {"field": "citizenship", "operator": "==", "value": "US"},
                {"field": "foreign_income", "operator": ">", "value": 100000},
            ]},
            risk_level=RiskLevel.high,
        )
        result = run_evaluation(client, [rule], {"citizenship": "US"})
        assert result["incomplete_rules"][0]["missing_fields"] == ["foreign_income"]

    def test_is_empty_does_not_trigger_incomplete_when_field_missing(self):
        """is_empty/not_empty operators have defined behavior on missing data —
        they should never cause a rule to be flagged incomplete."""
        client = SimpleNamespace(id=1)
        rule = make_rule_with_source(
            rule_code="EMPTY_CHECK",
            condition_expression={"field": "notes", "operator": "is_empty"},
            risk_level=RiskLevel.low,
        )
        result = run_evaluation(client, [rule], {})
        assert result["incomplete_rules"] == []


# ═══════════════════════════════════════════════════════════════════════════
# schemas/rule.py — write-time condition validation
# ═══════════════════════════════════════════════════════════════════════════

class TestConditionValidationFunction:
    """Unit tests for the _validate_condition_node helper."""

    def test_valid_leaf(self):
        _validate_condition_node({"field": "x", "operator": ">=", "value": 10})

    def test_valid_group(self):
        _validate_condition_node({
            "all": [{"field": "x", "operator": "==", "value": 1}]
        })

    def test_empty_dict_raises(self):
        with pytest.raises(ValueError, match="empty condition"):
            _validate_condition_node({})

    def test_missing_field_raises(self):
        with pytest.raises(ValueError, match="missing required key 'field'"):
            _validate_condition_node({"operator": "==", "value": 1})

    def test_missing_operator_raises(self):
        with pytest.raises(ValueError, match="missing required key 'operator'"):
            _validate_condition_node({"field": "x", "value": 1})

    def test_unsupported_operator_raises(self):
        with pytest.raises(ValueError, match="unsupported operator"):
            _validate_condition_node({"field": "x", "operator": "~=", "value": 1})

    def test_missing_value_for_comparison_raises(self):
        with pytest.raises(ValueError, match="requires a 'value' key"):
            _validate_condition_node({"field": "x", "operator": ">="})

    def test_is_empty_does_not_require_value(self):
        _validate_condition_node({"field": "x", "operator": "is_empty"})

    def test_not_empty_does_not_require_value(self):
        _validate_condition_node({"field": "x", "operator": "not_empty"})

    def test_group_with_non_list_raises(self):
        with pytest.raises(ValueError, match="must be a list"):
            _validate_condition_node({"all": "not a list"})

    def test_group_with_empty_list_raises(self):
        with pytest.raises(ValueError, match="at least one condition"):
            _validate_condition_node({"any": []})

    def test_nested_invalid_raises(self):
        with pytest.raises(ValueError, match="missing required key 'operator'"):
            _validate_condition_node({"all": [{"field": "x", "value": 1}]})

    def test_blank_field_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            _validate_condition_node({"field": "  ", "operator": "==", "value": 1})

    def test_non_dict_node_raises(self):
        with pytest.raises(ValueError, match="must be an object"):
            _validate_condition_node("not a dict")


class TestRuleCreateSchemaValidation:
    """Integration: Pydantic model rejects bad payloads at creation time."""

    VALID_BASE = {
        "rule_code": "TEST_001",
        "jurisdiction": "AU",
        "category": "residency",
        "description": "Test",
        "risk_level": "high",
        "confidence_level": "high",
        "source_id": 1,
        "version": 1,
        "effective_from": "2025-01-01",
    }

    def test_valid_condition_accepted(self):
        payload = {**self.VALID_BASE, "condition_expression": {"field": "x", "operator": ">=", "value": 183}}
        rule = RuleCreate(**payload)
        assert rule.condition_expression["field"] == "x"

    def test_invalid_condition_rejected(self):
        payload = {**self.VALID_BASE, "condition_expression": {"bad": "shape"}}
        with pytest.raises(Exception):
            RuleCreate(**payload)

    def test_empty_condition_rejected(self):
        payload = {**self.VALID_BASE, "condition_expression": {}}
        with pytest.raises(Exception):
            RuleCreate(**payload)

    def test_effective_to_before_from_rejected(self):
        payload = {
            **self.VALID_BASE,
            "condition_expression": {"field": "x", "operator": ">=", "value": 1},
            "effective_from": "2025-06-01",
            "effective_to": "2025-01-01",
        }
        with pytest.raises(Exception):
            RuleCreate(**payload)

    def test_effective_to_equal_from_accepted(self):
        payload = {
            **self.VALID_BASE,
            "condition_expression": {"field": "x", "operator": ">=", "value": 1},
            "effective_from": "2025-06-01",
            "effective_to": "2025-06-01",
        }
        rule = RuleCreate(**payload)
        assert rule.effective_from == rule.effective_to

    def test_unsupported_operator_in_condition_rejected(self):
        payload = {**self.VALID_BASE, "condition_expression": {"field": "x", "operator": "LIKE", "value": "%foo%"}}
        with pytest.raises(Exception):
            RuleCreate(**payload)
