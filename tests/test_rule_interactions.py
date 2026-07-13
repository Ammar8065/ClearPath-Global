"""Rule-interaction tests.

    app/engine/interactions.py — find_interactions, pure + defensive
    app/engine/report.py        — run_evaluation wires interactions through
    app/services/evaluation.py  — DB-backed loading and end-to-end wiring
    app/services/report_html.py — Interacting Findings section rendering
    seed_data.py                 — dangling rule_code fails loudly at seed time
"""
from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.engine.interactions import find_interactions
from app.engine.report import run_evaluation
from app.main import app
from app.models.rule import ConfidenceLevel, RiskLevel, RuleCategory

client = TestClient(app)


def make_source(source_id: int = 1, title: str = "Test Source", url: str = "https://example.com/source"):
    return SimpleNamespace(id=source_id, title=title, url=url)


def make_rule_with_source(*, source=None, **kwargs):
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


def make_interaction(**kwargs):
    defaults = {
        "primary_rule_code": kwargs.get("primary_rule_code", "A"),
        "related_rule_code": kwargs.get("related_rule_code", "B"),
        "interaction_type": kwargs.get("interaction_type", "relief"),
        "note": kwargs.get("note", "A note."),
    }
    return SimpleNamespace(**defaults)


# ═══════════════════════════════════════════════════════════════════════════
# app/engine/interactions.py — find_interactions
# ═══════════════════════════════════════════════════════════════════════════

class TestFindInteractions:
    def test_matches_when_both_sides_triggered(self):
        interactions = [make_interaction(primary_rule_code="A", related_rule_code="B")]
        found, warnings = find_interactions({"A", "B"}, interactions)
        assert len(found) == 1
        assert found[0]["primary_rule_code"] == "A"
        assert found[0]["related_rule_code"] == "B"
        assert warnings == []

    def test_no_match_when_only_primary_triggered(self):
        interactions = [make_interaction(primary_rule_code="A", related_rule_code="B")]
        found, warnings = find_interactions({"A"}, interactions)
        assert found == []
        assert warnings == []

    def test_no_match_when_only_related_triggered(self):
        interactions = [make_interaction(primary_rule_code="A", related_rule_code="B")]
        found, warnings = find_interactions({"B"}, interactions)
        assert found == []

    def test_no_match_when_neither_triggered(self):
        interactions = [make_interaction(primary_rule_code="A", related_rule_code="B")]
        found, warnings = find_interactions(set(), interactions)
        assert found == []

    def test_multiple_interactions_filtered_independently(self):
        interactions = [
            make_interaction(primary_rule_code="A", related_rule_code="B"),
            make_interaction(primary_rule_code="C", related_rule_code="D"),
        ]
        found, _ = find_interactions({"A", "B"}, interactions)
        assert len(found) == 1
        assert found[0]["primary_rule_code"] == "A"

    def test_accepts_dict_rows_not_just_orm_objects(self):
        interactions = [{
            "primary_rule_code": "A", "related_rule_code": "B",
            "interaction_type": "exception", "note": "A dict-shaped row.",
        }]
        found, warnings = find_interactions({"A", "B"}, interactions)
        assert len(found) == 1
        assert found[0]["interaction_type"] == "exception"
        assert warnings == []

    def test_interaction_type_enum_normalized_to_lowercase_string(self):
        interactions = [make_interaction(interaction_type=SimpleNamespace(value="RELIEF"))]
        found, _ = find_interactions({"A", "B"}, interactions)
        assert found[0]["interaction_type"] == "relief"

    def test_missing_field_skipped_with_warning_not_raised(self):
        bad = {"primary_rule_code": "A", "related_rule_code": "B", "interaction_type": "relief"}  # no note
        found, warnings = find_interactions({"A", "B"}, [bad])
        assert found == []
        assert len(warnings) == 1
        assert "note" in warnings[0]  # names the absent field, however it's categorized

    def test_falsy_but_present_field_reported_as_missing(self):
        """A field that's present but empty (not absent) hits the separate
        falsy-value guard rather than the KeyError path."""
        bad = {"primary_rule_code": "A", "related_rule_code": "B",
               "interaction_type": "relief", "note": ""}
        found, warnings = find_interactions({"A", "B"}, [bad])
        assert found == []
        assert len(warnings) == 1
        assert "missing field" in warnings[0].lower()

    def test_malformed_row_skipped_with_warning_not_raised(self):
        """A row that isn't even the right shape must not crash evaluation."""
        found, warnings = find_interactions({"A", "B"}, [object()])
        assert found == []
        assert len(warnings) == 1

    def test_dangling_rule_code_simply_never_matches(self):
        """A relationship referencing a rule that no longer exists/wasn't
        triggered degrades to a silent no-match, not an error."""
        interactions = [make_interaction(primary_rule_code="GONE", related_rule_code="B")]
        found, warnings = find_interactions({"B"}, interactions)
        assert found == []
        assert warnings == []

    def test_empty_interactions_list_is_a_noop(self):
        found, warnings = find_interactions({"A", "B"}, [])
        assert found == []
        assert warnings == []

    def test_multiple_interactions_on_same_primary_all_surfaced(self):
        """One triggered rule can be modified by several other triggered rules
        at once (e.g. UAE 9% CT with both SBR relief and QFZP exception in
        play) — every applicable pair is listed independently; the engine
        never nets them off or picks a winner."""
        interactions = [
            make_interaction(primary_rule_code="A", related_rule_code="B", interaction_type="relief"),
            make_interaction(primary_rule_code="A", related_rule_code="C", interaction_type="exception"),
        ]
        found, warnings = find_interactions({"A", "B", "C"}, interactions)
        assert len(found) == 2
        assert {f["related_rule_code"] for f in found} == {"B", "C"}
        assert warnings == []

    def test_chained_interactions_listed_pairwise_without_transitive_inference(self):
        """A←B and B←C both surface as separate pairs; the engine never
        derives an implied A←C relationship that nobody curated."""
        interactions = [
            make_interaction(primary_rule_code="A", related_rule_code="B"),
            make_interaction(primary_rule_code="B", related_rule_code="C"),
        ]
        found, _ = find_interactions({"A", "B", "C"}, interactions)
        pairs = {(f["primary_rule_code"], f["related_rule_code"]) for f in found}
        assert pairs == {("A", "B"), ("B", "C")}

    def test_self_referencing_interaction_skipped_with_warning(self):
        interactions = [make_interaction(primary_rule_code="A", related_rule_code="A")]
        found, warnings = find_interactions({"A"}, interactions)
        assert found == []
        assert len(warnings) == 1
        assert "references itself" in warnings[0]


# ═══════════════════════════════════════════════════════════════════════════
# app/engine/report.py — run_evaluation wiring
# ═══════════════════════════════════════════════════════════════════════════

class TestRunEvaluationInteractions:
    def test_interactions_surfaced_when_both_rules_trigger(self):
        client_obj = SimpleNamespace(id=1)
        rules = [
            make_rule_with_source(rule_code="UAE_TAX_001", condition_expression={"field": "x", "operator": "==", "value": True}),
            make_rule_with_source(rule_code="UAE_TAX_002", condition_expression={"field": "y", "operator": "==", "value": True}),
        ]
        interactions = [make_interaction(
            primary_rule_code="UAE_TAX_001", related_rule_code="UAE_TAX_002",
            interaction_type="relief", note="SBR can zero the 9% CT liability.",
        )]
        result = run_evaluation(client_obj, rules, {"x": True, "y": True}, interactions)
        assert len(result["rule_interactions"]) == 1
        assert result["rule_interactions"][0]["note"] == "SBR can zero the 9% CT liability."

    def test_no_interactions_when_only_one_rule_triggers(self):
        client_obj = SimpleNamespace(id=1)
        rules = [
            make_rule_with_source(rule_code="UAE_TAX_001", condition_expression={"field": "x", "operator": "==", "value": True}),
            make_rule_with_source(rule_code="UAE_TAX_002", condition_expression={"field": "y", "operator": "==", "value": True}),
        ]
        interactions = [make_interaction(primary_rule_code="UAE_TAX_001", related_rule_code="UAE_TAX_002")]
        result = run_evaluation(client_obj, rules, {"x": True, "y": False}, interactions)
        assert result["rule_interactions"] == []

    def test_interactions_default_to_empty_when_omitted(self):
        """Backward compatible: existing callers that don't pass interactions still work."""
        client_obj = SimpleNamespace(id=1)
        rule = make_rule_with_source(condition_expression={"field": "x", "operator": ">=", "value": 1})
        result = run_evaluation(client_obj, [rule], {"x": 5})
        assert result["rule_interactions"] == []

    def test_malformed_interaction_adds_warning_without_crashing_evaluation(self):
        client_obj = SimpleNamespace(id=1)
        rule = make_rule_with_source(rule_code="R1", condition_expression={"field": "x", "operator": ">=", "value": 1})
        result = run_evaluation(client_obj, [rule], {"x": 5}, [object()])
        assert result["triggered_rules"] == ["R1"]  # evaluation still completes
        assert result["rule_interactions"] == []
        assert any("malformed" in w.lower() for w in result["warnings"])


# ═══════════════════════════════════════════════════════════════════════════
# app/services/evaluation.py + full HTTP stack — real DB
# ═══════════════════════════════════════════════════════════════════════════

class TestEvaluationEndpointInteractions:
    def test_seeded_uae_relief_pair_surfaces_in_private_evaluation(self):
        """UAE_TAX_001/UAE_TAX_002 are seeded in seed_rule_interactions.py —
        drive facts that trigger both and confirm the interaction appears."""
        response = client.post("/evaluate/private", json={
            "client_data": {
                "uae_business_owned": True,
                "uae_taxable_income": 500000,
                "uae_revenue": 1000000,
            },
        })
        assert response.status_code == 200
        body = response.json()
        assert "UAE_TAX_001" in body["triggered_rules"]
        assert "UAE_TAX_002" in body["triggered_rules"]
        interaction = next(
            (i for i in body["rule_interactions"]
             if i["primary_rule_code"] == "UAE_TAX_001" and i["related_rule_code"] == "UAE_TAX_002"),
            None,
        )
        assert interaction is not None
        assert interaction["interaction_type"] == "relief"
        assert "small business relief" in interaction["note"].lower() or "sbr" in interaction["note"].lower() or "9%" in interaction["note"]

    def test_no_interactions_key_absent_when_nothing_triggers(self):
        response = client.post("/evaluate/private", json={"client_data": {}})
        assert response.status_code == 200
        assert response.json()["rule_interactions"] == []


# ═══════════════════════════════════════════════════════════════════════════
# app/schemas/evaluation.py
# ═══════════════════════════════════════════════════════════════════════════

def test_evaluation_response_rule_interactions_defaults_to_empty_list():
    from app.schemas.evaluation import EvaluationResponse

    resp = EvaluationResponse(
        client_id=None, overall_risk="low", score=0.0, triggered_rules=[],
        summary=[], category_breakdown={}, jurisdiction_breakdown={}, citations=[],
    )
    assert resp.rule_interactions == []


# ═══════════════════════════════════════════════════════════════════════════
# app/services/report_html.py
# ═══════════════════════════════════════════════════════════════════════════

def test_report_html_renders_interacting_findings_section():
    from app.services.report_html import generate_report_html

    result = {
        "assessment_label": "Interaction test", "overall_risk": "high", "score": 66.5,
        "triggered_rules": ["UAE_TAX_001", "UAE_TAX_002"],
        "summary": [
            {"rule_code": "UAE_TAX_001", "description": "9% CT", "risk_level": "high",
             "confidence_level": "high", "jurisdiction": "UAE", "category": "tax",
             "rule_score": 100.0, "source_id": 1, "source_title": "UAE Gov",
             "source_url": "https://u.ae", "section_reference": "Art 3",
             "review_status": "verified_current"},
        ],
        "category_breakdown": {}, "jurisdiction_breakdown": {},
        "citations": [], "incomplete_rules": [], "warnings": [],
        "rule_interactions": [{
            "primary_rule_code": "UAE_TAX_001", "related_rule_code": "UAE_TAX_002",
            "interaction_type": "relief", "note": "SBR election can zero the 9% CT liability.",
        }],
    }
    html = generate_report_html(result, fact_count=3)
    assert "Interacting Findings" in html
    assert "Relief Available" in html
    assert "SBR election can zero the 9% CT liability." in html
    assert "UAE_TAX_001" in html and "UAE_TAX_002" in html


def test_report_html_omits_interactions_section_when_none_found():
    from app.services.report_html import generate_report_html

    result = {
        "assessment_label": "No interactions", "overall_risk": "low", "score": 0.0,
        "triggered_rules": [], "summary": [], "category_breakdown": {},
        "jurisdiction_breakdown": {}, "citations": [], "incomplete_rules": [],
        "warnings": [], "rule_interactions": [],
    }
    html = generate_report_html(result, fact_count=0)
    assert "Interacting Findings" not in html


# ═══════════════════════════════════════════════════════════════════════════
# seed_data.py — dangling rule_code must fail loudly at seed time
# ═══════════════════════════════════════════════════════════════════════════

def test_seed_rejects_interaction_referencing_unknown_rule_code(monkeypatch):
    import seed_data

    fake_fixtures = [{
        "primary_rule_code": "DOES_NOT_EXIST", "related_rule_code": "AU_RES_001",
        "interaction_type": "relief", "note": "x",
    }]
    monkeypatch.setattr(seed_data, "RULE_INTERACTION_FIXTURES", fake_fixtures)

    with pytest.raises(ValueError, match="DOES_NOT_EXIST"):
        seed_data.upsert_rule_interactions()


def test_seed_rejects_self_referencing_interaction(monkeypatch):
    import seed_data

    fake_fixtures = [{
        "primary_rule_code": "AU_RES_001", "related_rule_code": "AU_RES_001",
        "interaction_type": "relief", "note": "x",
    }]
    monkeypatch.setattr(seed_data, "RULE_INTERACTION_FIXTURES", fake_fixtures)

    with pytest.raises(ValueError, match="references itself"):
        seed_data.upsert_rule_interactions()


def test_seeded_multi_interaction_pileup_on_one_primary_rule():
    """End-to-end: UAE facts that trigger the 9% CT rule plus BOTH of its
    curated modifiers (SBR relief and QFZP exception) surface two independent
    interaction entries against UAE_TAX_001 — including the mutually
    exclusive pair (a QFZP-electing entity is excluded from SBR, which the
    relief note itself states). The engine presents both; the advisor decides."""
    response = client.post("/evaluate/private", json={
        "client_data": {
            "uae_business_owned": True,
            "uae_taxable_income": 900000,
            "uae_revenue": 1500000,
            "uae_freezone_entity": True,
            "uae_non_qualifying_income": 0,
        },
    })
    assert response.status_code == 200
    body = response.json()
    assert {"UAE_TAX_001", "UAE_TAX_002", "UAE_TAX_006"} <= set(body["triggered_rules"])

    on_primary = [i for i in body["rule_interactions"] if i["primary_rule_code"] == "UAE_TAX_001"]
    assert {i["related_rule_code"] for i in on_primary} == {"UAE_TAX_002", "UAE_TAX_006"}
    assert {i["interaction_type"] for i in on_primary} == {"relief", "exception"}
