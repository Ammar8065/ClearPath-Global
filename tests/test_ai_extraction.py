"""Unit tests for AI extraction — Anthropic client fully stubbed, no network."""
from __future__ import annotations

from types import SimpleNamespace

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai.client import AIResponseError
from app.services.ai.extraction import ExtractedFact, ExtractionOutput, extract_client_data

# Plain TestClient (no context manager) skips lifespan, so no database is needed
# for the stateless /ai routes.
client = TestClient(app)


class _StubMessages:
    def __init__(self, response=None, error: Exception | None = None):
        self._response = response
        self._error = error
        self.calls: list[dict] = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return self._response


class _StubClient:
    def __init__(self, response=None, error: Exception | None = None):
        self.messages = _StubMessages(response, error)


def _fake_response(parsed, *, stop_reason="end_turn", model="claude-test"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        parsed_output=parsed,
        model=model,
        usage=SimpleNamespace(
            input_tokens=100,
            output_tokens=50,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )


def _patch_client(monkeypatch, stub: _StubClient) -> None:
    monkeypatch.setattr("app.services.ai.extraction.get_client", lambda: stub)


def test_extraction_validates_and_coerces(monkeypatch):
    output = ExtractionOutput(
        facts=[
            ExtractedFact(field="days_in_country", value=190, evidence="spent 190 days in Australia"),
            ExtractedFact(field="australian_property_owned", value=True, evidence="owns a Sydney flat"),
            ExtractedFact(field="citizenship", value="us", evidence="US citizen"),
            ExtractedFact(field="tax_residency_status", value="Resident", evidence="treated as a resident"),
            ExtractedFact(field="not_a_real_field", value=True, evidence="…"),
            ExtractedFact(field="domicile_country", value="France", evidence="domiciled in France"),
            ExtractedFact(field="worldwide_income", value=True, evidence="has income"),
            ExtractedFact(field="days_in_country", value=200, evidence="duplicate"),
        ],
        unmapped_notes=["Considering moving the trust to Jersey next year."],
    )
    _patch_client(monkeypatch, _StubClient(_fake_response(output)))

    result = extract_client_data("some notes")

    assert result["client_data"] == {
        "days_in_country": 190.0,
        "australian_property_owned": True,
        "citizenship": "US",
        "tax_residency_status": "resident",
    }
    assert [f["field"] for f in result["facts"]] == [
        "days_in_country",
        "australian_property_owned",
        "citizenship",
        "tax_residency_status",
    ]
    fact = result["facts"][0]
    assert fact["label"].startswith("How many days")
    assert fact["evidence"] == "spent 190 days in Australia"
    # unknown field, bad enum, bool-as-number, duplicate → four warnings
    assert len(result["warnings"]) == 4
    assert result["unmapped_notes"] == ["Considering moving the trust to Jersey next year."]
    assert result["model"] == "claude-test"
    assert result["usage"]["input_tokens"] == 100


def test_extraction_prompt_contains_notes_and_catalog(monkeypatch):
    stub = _StubClient(_fake_response(ExtractionOutput(facts=[], unmapped_notes=[])))
    _patch_client(monkeypatch, stub)

    extract_client_data("client spent 190 days abroad")

    call = stub.messages.calls[0]
    assert "client spent 190 days abroad" in call["messages"][0]["content"]
    system_text = call["system"][0]["text"]
    assert "days_in_country" in system_text
    assert "us_state_residency" in system_text
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert call["output_format"] is ExtractionOutput


def test_extraction_refusal_raises(monkeypatch):
    _patch_client(monkeypatch, _StubClient(_fake_response(None, stop_reason="refusal")))
    with pytest.raises(AIResponseError, match="declined"):
        extract_client_data("notes")


def test_extraction_unparseable_output_raises(monkeypatch):
    _patch_client(monkeypatch, _StubClient(_fake_response(None)))
    with pytest.raises(AIResponseError, match="structured output"):
        extract_client_data("notes")


def test_extract_endpoint_503_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/ai/extract", json={"notes": "some notes"})
    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_extract_endpoint_rejects_blank_notes(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    response = client.post("/ai/extract", json={"notes": "   "})
    assert response.status_code == 422


def test_extract_endpoint_happy_path(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    output = ExtractionOutput(
        facts=[ExtractedFact(field="days_in_country", value=185, evidence="185 days")],
        unmapped_notes=[],
    )
    _patch_client(monkeypatch, _StubClient(_fake_response(output)))

    response = client.post("/ai/extract", json={"notes": "client spent 185 days in AU"})

    assert response.status_code == 200
    body = response.json()
    assert body["client_data"] == {"days_in_country": 185.0}
    assert body["facts"][0]["evidence"] == "185 days"
    assert body["warnings"] == []
    # usage is service-internal detail and is filtered out of the API response
    assert "usage" not in body


def test_eval_harness_scoring():
    from eval_ai_extraction import score_case

    expected = {"a": 1, "b": True, "c": "AU"}
    extracted = {"a": 1.0, "b": False, "d": 5}

    scores = score_case(expected, extracted)

    assert scores["correct"] == ["a"]
    assert scores["wrong_value"] == ["b"]
    assert scores["hallucinated"] == ["d"]
    assert scores["missed"] == ["c"]
    assert scores["precision"] == pytest.approx(1 / 3)
    assert scores["recall"] == pytest.approx(1 / 3)

    # empty vs empty is a perfect score (the hallucination-probe case)
    empty = score_case({}, {})
    assert empty["precision"] == 1.0
    assert empty["recall"] == 1.0

    # bool/number crossover must not count as equal
    assert score_case({"x": 1}, {"x": True})["wrong_value"] == ["x"]


def test_golden_fixture_integrity():
    """Every expected field in the golden cases must be a valid catalog value."""
    import json
    from pathlib import Path

    from app.services.ai.field_catalog import FIELD_CATALOG, coerce_value

    fixture = Path(__file__).resolve().parent / "fixtures" / "ai_extraction_cases.json"
    cases = json.loads(fixture.read_text(encoding="utf-8"))["cases"]

    assert len(cases) >= 8
    ids = [case["id"] for case in cases]
    assert len(set(ids)) == len(ids), "duplicate case ids"
    assert any(not case["expected_client_data"] for case in cases), "keep a hallucination probe"

    for case in cases:
        assert case["notes"].strip()
        for key, value in case["expected_client_data"].items():
            spec = FIELD_CATALOG.get(key)
            assert spec is not None, f"{case['id']}: unknown field {key!r}"
            _, error = coerce_value(spec, value)
            assert error is None, f"{case['id']}: {key}: {error}"


def test_extract_endpoint_maps_sdk_errors(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    request = httpx.Request("POST", "http://test")

    cases = [
        (anthropic.RateLimitError("rate limited", response=httpx.Response(429, request=request), body=None), 429),
        (anthropic.APIConnectionError(request=request), 503),
        (anthropic.InternalServerError("boom", response=httpx.Response(500, request=request), body=None), 502),
    ]
    for error, expected_status in cases:
        _patch_client(monkeypatch, _StubClient(error=error))
        response = client.post("/ai/extract", json={"notes": "notes"})
        assert response.status_code == expected_status, error
