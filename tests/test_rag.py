"""Unit tests for RAG retrieval/answering — Chroma and Anthropic client fully
stubbed, no network and no dependency on the real rag/chroma_db/ store."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai.client import AIResponseError
from app.services.rag.answer import RAGModelOutput, answer_question

client = TestClient(app)

FAKE_CONTEXT = {
    "rules": [
        {
            "document": "[AU_RES_001] (AU / residency) Physical presence for 183 days...",
            "rule_code": "AU_RES_001",
            "jurisdiction": "AU",
            "category": "residency",
            "risk_level": "high",
            "confidence_level": "high",
            "condition_expression": "{}",
            "section_reference": "s. 995-1 ITAA 1997",
            "source_key": "AU_ATO_RESIDENCY",
            "source_title": "ATO — Tax residency guidance for individuals",
            "source_url": "https://example.com/ato-residency",
        }
    ],
    "chunks": [
        {
            "document": "The 183-day test is a primary residency trigger...",
            "source_key": "AU_ATO_RESIDENCY",
            "title": "ATO — Tax residency guidance for individuals",
            "url": "https://example.com/ato-residency",
            "jurisdiction": "AU",
            "chunk_index": 0,
        }
    ],
}

FAKE_OUTPUT = RAGModelOutput(
    answer="Physical presence of 183 days or more in Australia triggers the statutory residency test.",
    cited_rule_codes=["AU_RES_001"],
    cited_source_keys=["AU_ATO_RESIDENCY"],
    caveat=None,
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


def _patch(monkeypatch, *, response=None, context=FAKE_CONTEXT):
    monkeypatch.setattr("app.services.rag.answer.retrieve_context", lambda question, **kw: context)
    if response is not None:
        monkeypatch.setattr("app.services.rag.answer.get_client", lambda: _StubClient(response))


# ── answer_question (service-level) ─────────────────────────────────────────


def test_answer_question_builds_citations_from_retrieved_context(monkeypatch):
    _patch(monkeypatch, response=_fake_response(FAKE_OUTPUT))

    result = answer_question("What triggers Australian tax residency?")

    assert result["answer"].startswith("Physical presence")
    assert result["caveat"] is None
    assert result["model"] == "claude-test"
    assert {c["type"] for c in result["citations"]} == {"rule", "source"}
    rule_citation = next(c for c in result["citations"] if c["type"] == "rule")
    assert rule_citation["key"] == "AU_RES_001"
    assert rule_citation["url"] == "https://example.com/ato-residency"


def test_answer_question_drops_fabricated_citations(monkeypatch):
    """A rule_code/source_key the model names but that was never retrieved must
    never surface as a citation — it would be an ungrounded, possibly invented link."""
    hallucinated = RAGModelOutput(
        answer="...",
        cited_rule_codes=["AU_RES_001", "US_MADE_UP_999"],
        cited_source_keys=["AU_ATO_RESIDENCY", "NOT_A_REAL_SOURCE"],
        caveat=None,
    )
    _patch(monkeypatch, response=_fake_response(hallucinated))

    result = answer_question("irrelevant")

    keys = {c["key"] for c in result["citations"]}
    assert keys == {"AU_RES_001", "AU_ATO_RESIDENCY"}


def test_answer_question_refusal_raises(monkeypatch):
    _patch(monkeypatch, response=_fake_response(None, stop_reason="refusal"))
    with pytest.raises(AIResponseError, match="declined"):
        answer_question("irrelevant")


def test_answer_question_sends_retrieved_context_to_model(monkeypatch):
    stub = _StubClient(_fake_response(FAKE_OUTPUT))
    monkeypatch.setattr("app.services.rag.answer.retrieve_context", lambda question, **kw: FAKE_CONTEXT)
    monkeypatch.setattr("app.services.rag.answer.get_client", lambda: stub)

    answer_question("What triggers Australian tax residency?")

    call = stub.messages.calls[0]
    user_content = call["messages"][0]["content"]
    assert "AU_RES_001" in user_content
    assert "183-day test is a primary residency trigger" in user_content
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}


# ── /rag/status ──────────────────────────────────────────────────────────────


def test_rag_status_reports_unavailable_db(monkeypatch):
    monkeypatch.setattr("app.routes.rag.vector_db_available", lambda: False)
    response = client.get("/rag/status")
    assert response.status_code == 200
    body = response.json()
    assert body["vector_db_available"] is False
    assert body["rule_count"] == 0
    assert body["source_chunk_count"] == 0


def test_rag_status_reports_available_db(monkeypatch):
    monkeypatch.setattr("app.routes.rag.vector_db_available", lambda: True)
    monkeypatch.setattr("app.routes.rag.collection_counts", lambda: (98, 1119))
    response = client.get("/rag/status")
    assert response.status_code == 200
    body = response.json()
    assert body["vector_db_available"] is True
    assert body["rule_count"] == 98
    assert body["source_chunk_count"] == 1119


# ── /rag/query ───────────────────────────────────────────────────────────────


def test_rag_query_503_when_db_missing(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("app.routes.rag.vector_db_available", lambda: False)
    response = client.post("/rag/query", json={"question": "What is the 183-day test?"})
    assert response.status_code == 503
    assert "vector database" in response.json()["detail"]


def test_rag_query_503_when_ai_unconfigured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("app.routes.rag.vector_db_available", lambda: True)
    response = client.post("/rag/query", json={"question": "What is the 183-day test?"})
    assert response.status_code == 503
    assert "AI assist" in response.json()["detail"]


def test_rag_query_happy_path(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("app.routes.rag.vector_db_available", lambda: True)
    _patch(monkeypatch, response=_fake_response(FAKE_OUTPUT))

    response = client.post("/rag/query", json={"question": "What triggers Australian tax residency?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("Physical presence")
    assert body["model"] == "claude-test"
    assert len(body["citations"]) == 2
    assert {c["type"] for c in body["citations"]} == {"rule", "source"}


def test_rag_query_blank_question_rejected():
    response = client.post("/rag/query", json={"question": "   "})
    assert response.status_code == 422


def test_rag_query_refusal_maps_to_422(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("app.routes.rag.vector_db_available", lambda: True)
    _patch(monkeypatch, response=_fake_response(None, stop_reason="refusal"))

    response = client.post("/rag/query", json={"question": "What triggers Australian tax residency?"})
    assert response.status_code == 422
