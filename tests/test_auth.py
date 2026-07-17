"""Auth and permission tests — Clerk verification fully stubbed, no network.

The autouse fixture in conftest.py clears the Clerk env vars, so tests here
re-enable auth explicitly where needed.
"""
from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.main import app
from app.models.knowledge_source import KnowledgeSource, SourceType
from app.models.rule import ConfidenceLevel, RiskLevel, Rule, RuleCategory
from app.services.auth import Session as AuthSession
from app.services.sources import delete_source

client = TestClient(app)

ADMIN_ID = "user_admin123"


def _enable_auth(monkeypatch):
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", "pk_test_fake")
    monkeypatch.setenv("ADMIN_USER_ID", ADMIN_ID)


def _stub_session(monkeypatch, session: AuthSession | None):
    """Stub token verification for both import sites of verify_request."""
    monkeypatch.setattr("app.services.auth.verify_request", lambda request: session)
    monkeypatch.setattr("app.routes.auth.verify_request", lambda request: session)


# ── Open mode (no Clerk configured) ─────────────────────────────


def test_status_reports_disabled_auth():
    body = client.get("/auth/status").json()
    assert body == {
        "auth_enabled": False,
        "authenticated": True,
        "user_id": "dev",
        "role": "admin",
        "publishable_key": None,
    }


def test_open_mode_allows_reads_and_admin_routes():
    assert client.get("/rules").status_code == 200
    # Admin gate passes in open mode; unknown id proves we reached the handler.
    assert client.delete("/sources/999999").status_code == 404


# ── Enabled: unauthenticated ────────────────────────────────────


def test_enabled_unauthenticated_gets_401(monkeypatch):
    _enable_auth(monkeypatch)
    _stub_session(monkeypatch, None)

    assert client.get("/rules").status_code == 401
    assert client.get("/sources").status_code == 401
    assert client.post("/rules", json={}).status_code == 401
    assert client.get("/ai/status").status_code == 401
    assert client.get("/rag/status").status_code == 401


def test_enabled_status_is_open_and_serves_publishable_key(monkeypatch):
    _enable_auth(monkeypatch)
    _stub_session(monkeypatch, None)

    response = client.get("/auth/status")
    assert response.status_code == 200
    body = response.json()
    assert body["auth_enabled"] is True
    assert body["authenticated"] is False
    assert body["publishable_key"] == "pk_test_fake"


# ── Enabled: viewer ─────────────────────────────────────────────


def test_viewer_can_read_but_not_mutate(monkeypatch):
    _enable_auth(monkeypatch)
    _stub_session(monkeypatch, AuthSession(user_id="user_viewer", role="viewer"))

    assert client.get("/rules").status_code == 200
    assert client.post("/rules", json={}).status_code == 403
    assert client.delete("/rules/1").status_code == 403
    assert client.post("/sources", json={}).status_code == 403
    assert client.delete("/sources/1").status_code == 403


def test_viewer_status_reports_viewer_role(monkeypatch):
    _enable_auth(monkeypatch)
    _stub_session(monkeypatch, AuthSession(user_id="user_viewer", role="viewer"))

    body = client.get("/auth/status").json()
    assert body["authenticated"] is True
    assert body["role"] == "viewer"


# ── Enabled: admin ──────────────────────────────────────────────


def test_admin_passes_mutation_gate(monkeypatch):
    _enable_auth(monkeypatch)
    _stub_session(monkeypatch, AuthSession(user_id=ADMIN_ID, role="admin"))

    # 404 (not 401/403) proves authz passed and the handler ran.
    assert client.delete("/sources/999999").status_code == 404
    assert client.delete("/rules/999999").status_code == 404


def test_admin_role_derived_from_admin_user_id(monkeypatch):
    """verify_request maps sub == ADMIN_USER_ID to the admin role."""
    from app.services import auth as auth_service

    _enable_auth(monkeypatch)

    class FakeState:
        is_signed_in = True

        def __init__(self, sub):
            self.payload = {"sub": sub}

    class FakeClerk:
        def __init__(self, sub):
            self._sub = sub

        def authenticate_request(self, request, options):
            return FakeState(self._sub)

    monkeypatch.setattr(auth_service, "_clerk", lambda: FakeClerk(ADMIN_ID))
    session = auth_service.verify_request(None)
    assert session == AuthSession(user_id=ADMIN_ID, role="admin")

    monkeypatch.setattr(auth_service, "_clerk", lambda: FakeClerk("user_someone_else"))
    session = auth_service.verify_request(None)
    assert session == AuthSession(user_id="user_someone_else", role="viewer")


# ── delete_source service semantics ─────────────────────────────


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    yield session
    session.close()


def test_delete_source_blocked_while_referenced(db_session):
    source = KnowledgeSource(
        jurisdiction="AU",
        title="ATO guidance",
        url="https://example.com/ato",
        source_type=SourceType.government_guidance,
    )
    db_session.add(source)
    db_session.commit()

    rule = Rule(
        rule_code="AU_TEST_001",
        jurisdiction="AU",
        category=RuleCategory.residency,
        condition_expression={"field": "days_in_country", "operator": ">=", "value": 183},
        description="Test rule",
        risk_level=RiskLevel.low,
        confidence_level=ConfidenceLevel.low,
        effective_from=date(2024, 1, 1),
        source_id=source.id,
    )
    db_session.add(rule)
    db_session.commit()

    with pytest.raises(ValueError, match="referenced by 1 rule"):
        delete_source(db_session, source.id)

    # Remove the referencing rule; deletion then succeeds.
    db_session.delete(rule)
    db_session.commit()
    deleted = delete_source(db_session, source.id)
    assert deleted.id == source.id
    assert db_session.get(KnowledgeSource, source.id) is None


def test_delete_source_missing_raises_lookup(db_session):
    with pytest.raises(LookupError):
        delete_source(db_session, 12345)
