"""Unit tests for AI summarisation — Anthropic client fully stubbed, no network."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai.client import AIResponseError
from app.services.ai.summarisation import (
    AISummary,
    RuleExplanation,
    _enrich_with_source_excerpts,
    _summary_payload,
    summarise_evaluation,
)

client = TestClient(app)

LABEL_SENTINEL = "SENTINEL Jane Citizen — Matter 24-017"
VALUE_SENTINEL = "SENTINEL-9876543"

EVAL_RESULT = {
    "client_id": None,
    "assessment_label": LABEL_SENTINEL,
    "overall_risk": "high",
    "score": 74.25,
    "triggered_rules": ["AU_RES_001"],
    "summary": [
        {
            "rule_code": "AU_RES_001",
            "description": "183-day statutory test for Australian tax residency.",
            "risk_level": "high",
            "confidence_level": "high",
            "jurisdiction": "AU",
            "category": "residency",
            "rule_score": 100.0,
            "source_id": 1,
            "source_title": "ATO — Tax residency guidance for individuals",
            "source_url": "https://example.com/ato",
            "section_reference": "s. 995-1 ITAA 1997",
            "review_status": "verified_current",
        }
    ],
    "category_breakdown": {
        "residency": {"score": 100.0, "triggered_count": 1, "max_risk": "high"},
        "tax": {"score": 0.0, "triggered_count": 0, "max_risk": "low"},
        "cross_border": {"score": 0.0, "triggered_count": 0, "max_risk": "low"},
        "structure": {"score": 0.0, "triggered_count": 0, "max_risk": "low"},
    },
    "jurisdiction_breakdown": {"AU": {"score": 100.0, "triggered_count": 1}},
    "citations": [
        {
            "rule_code": "AU_RES_001",
            "source_title": "ATO — Tax residency guidance for individuals",
            "source_url": "https://example.com/ato",
            "jurisdiction": "AU",
            "section_reference": "s. 995-1 ITAA 1997",
        }
    ],
    "incomplete_rules": [
        {
            "rule_code": "AU_TAX_002",
            "description": "Medicare levy surcharge exposure.",
            "risk_level": "medium",
            "jurisdiction": "AU",
            "category": "tax",
            "missing_fields": ["worldwide_income"],
            "reason": "Cannot evaluate — missing: worldwide_income",
        }
    ],
    "warnings": [],
}

FAKE_SUMMARY = AISummary(
    headline="High residency risk driven by the 183-day test.",
    overview="The client's day count triggers the statutory residency test.",
    key_risks=["Australian tax residency is likely established."],
    recommended_actions=["Confirm worldwide income to assess surcharge exposure."],
    rule_explanations=[RuleExplanation(rule_code="AU_RES_001", explanation="The 183-day test fired.")],
)


class _StubMessages:
    def __init__(self, response):
        self._response = response
        self.calls: list[dict] = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


class _StubClient:
    def __init__(self, response):
        self.messages = _StubMessages(response)


def _fake_response(parsed, *, stop_reason="end_turn", model="claude-test"):
    return SimpleNamespace(stop_reason=stop_reason, parsed_output=parsed, model=model)


def _patch_client(monkeypatch, stub: _StubClient) -> None:
    monkeypatch.setattr("app.services.ai.summarisation.get_client", lambda: stub)


def test_summary_payload_forwards_rule_interactions():
    """Curated interaction notes are rule-library metadata, not client data —
    they must reach the model so the narrative can connect the findings."""
    result = {
        **EVAL_RESULT,
        "rule_interactions": [{
            "primary_rule_code": "UAE_TAX_001", "related_rule_code": "UAE_TAX_002",
            "interaction_type": "relief", "note": "SBR can reduce the 9% CT to nil.",
        }],
    }
    payload = _summary_payload(result)
    assert payload["rule_interactions"] == [{
        "primary_rule_code": "UAE_TAX_001", "related_rule_code": "UAE_TAX_002",
        "interaction_type": "relief", "note": "SBR can reduce the 9% CT to nil.",
    }]


def test_summary_payload_excludes_client_identifying_data():
    """The privacy contract: only rule outcomes leave the machine."""
    result = {
        **EVAL_RESULT,
        # Even if a caller smuggles raw facts into the result dict, the payload
        # builder must not forward them.
        "client_data": {"worldwide_income": VALUE_SENTINEL},
    }

    rendered = json.dumps(_summary_payload(result))

    assert LABEL_SENTINEL not in rendered
    assert VALUE_SENTINEL not in rendered
    assert "AU_RES_001" in rendered
    assert "worldwide_income" in rendered  # missing-field *names* are rule metadata
    assert "reason" not in json.loads(rendered)["incomplete_rules"][0]


# ── Source-excerpt grounding ─────────────────────────────────────────────────


def test_enrich_attaches_excerpt_when_vector_db_has_a_match(monkeypatch):
    monkeypatch.setattr(
        "app.services.ai.summarisation.retrieve_excerpt_for_source",
        lambda description, source_url, n=1: [{"document": "The 183-day test is a primary trigger..."}],
    )
    payload = _summary_payload(EVAL_RESULT)

    enriched = _enrich_with_source_excerpts(payload)

    rule = enriched["triggered_rules"][0]
    assert rule["source_excerpt"] == "The 183-day test is a primary trigger..."
    assert "source_url" not in rule  # internal-only field, never sent to the model


def test_enrich_is_a_noop_when_vector_db_has_no_match(monkeypatch):
    monkeypatch.setattr(
        "app.services.ai.summarisation.retrieve_excerpt_for_source",
        lambda description, source_url, n=1: [],
    )
    payload = _summary_payload(EVAL_RESULT)

    enriched = _enrich_with_source_excerpts(payload)

    assert "source_excerpt" not in enriched["triggered_rules"][0]
    assert "source_url" not in enriched["triggered_rules"][0]


def test_enrich_tolerates_retrieval_failures(monkeypatch):
    def boom(description, source_url, n=1):
        raise RuntimeError("vector db unavailable")

    monkeypatch.setattr("app.services.ai.summarisation.retrieve_excerpt_for_source", boom)
    payload = _summary_payload(EVAL_RESULT)

    enriched = _enrich_with_source_excerpts(payload)  # must not raise

    assert "source_excerpt" not in enriched["triggered_rules"][0]


def test_summarise_sends_payload_not_raw_result(monkeypatch):
    stub = _StubClient(_fake_response(FAKE_SUMMARY))
    _patch_client(monkeypatch, stub)

    result = summarise_evaluation(EVAL_RESULT)

    call = stub.messages.calls[0]
    user_content = call["messages"][0]["content"]
    assert LABEL_SENTINEL not in user_content
    assert "AU_RES_001" in user_content
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert result["summary"]["headline"].startswith("High residency risk")
    assert result["summary"]["rule_explanations"][0]["rule_code"] == "AU_RES_001"
    assert result["model"] == "claude-test"


def test_summarise_refusal_raises(monkeypatch):
    _patch_client(monkeypatch, _StubClient(_fake_response(None, stop_reason="refusal")))
    with pytest.raises(AIResponseError, match="declined"):
        summarise_evaluation(EVAL_RESULT)


def test_summarise_endpoint_503_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/ai/summarise", json={"evaluation": EVAL_RESULT})
    assert response.status_code == 503


def test_summarise_endpoint_happy_path(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    _patch_client(monkeypatch, _StubClient(_fake_response(FAKE_SUMMARY)))

    response = client.post("/ai/summarise", json={"evaluation": EVAL_RESULT})

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["key_risks"] == ["Australian tax residency is likely established."]
    assert body["model"] == "claude-test"


# ── PDF report integration ──────────────────────────────────────────────────


def test_report_html_renders_ai_summary_section():
    from app.services.report_html import generate_report_html

    with_summary = generate_report_html(
        dict(EVAL_RESULT), fact_count=3, ai_summary=FAKE_SUMMARY.model_dump()
    )
    assert "Executive Summary" in with_summary
    assert "High residency risk driven by the 183-day test." in with_summary
    assert "Findings Explained" in with_summary
    assert "AI-Generated Summary" in with_summary

    without_summary = generate_report_html(dict(EVAL_RESULT), fact_count=3)
    assert "Executive Summary" not in without_summary


def _patch_report_pipeline(monkeypatch, captured: dict) -> None:
    def fake_generate(result, *, fact_count=0, ai_summary=None):
        captured["ai_summary"] = ai_summary
        captured["warnings"] = result["warnings"]
        captured["fact_count"] = fact_count
        return "<html></html>"

    monkeypatch.setattr(
        "app.routes.evaluation.evaluate_private_assessment",
        lambda db, data, assessment_label=None, jurisdiction_scope=None: dict(EVAL_RESULT),
    )
    monkeypatch.setattr("app.routes.evaluation.generate_report_html", fake_generate)
    monkeypatch.setattr("app.routes.evaluation.render_pdf", lambda html: b"%PDF-1.4 fake")


def test_report_includes_ai_summary_when_requested(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured: dict = {}
    _patch_report_pipeline(monkeypatch, captured)
    monkeypatch.setattr(
        "app.routes.evaluation.summarise_evaluation",
        lambda result: {"summary": FAKE_SUMMARY.model_dump(), "model": "claude-test"},
    )

    response = client.post(
        "/evaluate/private/report",
        json={"client_data": {"days_in_country": 190}, "include_ai_summary": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert captured["ai_summary"]["headline"].startswith("High residency risk")


def test_report_falls_back_when_ai_fails(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured: dict = {}
    _patch_report_pipeline(monkeypatch, captured)

    def boom(result):
        raise RuntimeError("AI unavailable")

    monkeypatch.setattr("app.routes.evaluation.summarise_evaluation", boom)

    response = client.post(
        "/evaluate/private/report",
        json={"client_data": {"days_in_country": 190}, "include_ai_summary": True},
    )

    assert response.status_code == 200
    assert captured["ai_summary"] is None
    assert any("AI summary" in warning for warning in captured["warnings"])


def test_report_skips_ai_when_not_requested(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured: dict = {}
    _patch_report_pipeline(monkeypatch, captured)

    def fail_if_called(result):
        raise AssertionError("summarise_evaluation must not be called")

    monkeypatch.setattr("app.routes.evaluation.summarise_evaluation", fail_if_called)

    response = client.post(
        "/evaluate/private/report",
        json={"client_data": {"days_in_country": 190}},
    )

    assert response.status_code == 200
    assert captured["ai_summary"] is None
    assert captured["warnings"] == []


def test_report_fact_count_treats_explicit_false_as_answered(monkeypatch):
    """An explicit "No" (False) and a zero are answered facts; only None and
    empty strings are unanswered. Keeps the PDF header consistent with the
    worksheet's tri-state counter."""
    captured: dict = {}
    _patch_report_pipeline(monkeypatch, captured)

    response = client.post(
        "/evaluate/private/report",
        json={
            "client_data": {
                "days_in_country": 0,                      # answered: zero
                "australian_property_owned": False,        # answered: explicit No
                "citizenship": "",                         # unanswered
                "worldwide_income": None,                  # unanswered
                "dual_tax_residency": True,                # answered
            }
        },
    )

    assert response.status_code == 200
    assert captured["fact_count"] == 3
