from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.database import init_db as init_db_module
from app.database.base import Base
from app.models.asset import Asset, AssetType, OwnershipStructure
from app.engine.conditions import evaluate_condition
from app.engine.report import run_evaluation
from app.models.client import Client
from app.models.rule import ConfidenceLevel, RiskLevel, RuleCategory
from app.models.tenant import Tenant
from app.schemas.asset import AssetCreate
from app.services.assets import create_asset, list_assets

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_is_empty_operator_without_value_evaluates_successfully():
    assert evaluate_condition({"field": "notes", "operator": "is_empty"}, {"notes": ""}) is True
    assert evaluate_condition({"field": "notes", "operator": "not_empty"}, {"notes": "ready"}) is True


def test_run_evaluation_triggers_is_empty_rule_without_warning():
    client = SimpleNamespace(id=1)
    source = SimpleNamespace(id=1, title="Test Source", url="https://example.com/source")
    rule = SimpleNamespace(
        rule_code="EMPTY_RULE",
        jurisdiction="AU",
        category=RuleCategory.tax,
        condition_expression={"field": "notes", "operator": "is_empty"},
        description="Empty notes should trigger",
        risk_level=RiskLevel.low,
        confidence_level=ConfidenceLevel.high,
        version=1,
        effective_from=None,
        effective_to=None,
        is_deleted=False,
        source_id=1,
        section_reference=None,
        source=source,
    )

    result = run_evaluation(client, [rule], {"notes": ""})

    assert result["triggered_rules"] == ["EMPTY_RULE"]
    assert result["warnings"] == []


def test_create_asset_rejects_soft_deleted_client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        tenant = Tenant(name="Deleted Client Tenant")
        db.add(tenant)
        db.flush()

        client = Client(
            tenant_id=tenant.id,
            citizenships=["AU"],
            current_residency="AU",
            is_deleted=True,
        )
        db.add(client)
        db.commit()
        db.refresh(client)

        with pytest.raises(HTTPException) as exc_info:
            create_asset(
                db,
                AssetCreate(
                    client_id=client.id,
                    type="cash",
                    location="AU",
                    ownership_structure="individual",
                ),
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Client not found."


def test_list_assets_filters_to_active_clients_and_requested_tenant():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        tenant_a = Tenant(name="Tenant A")
        tenant_b = Tenant(name="Tenant B")
        db.add_all([tenant_a, tenant_b])
        db.flush()

        active_client = Client(
            tenant_id=tenant_a.id,
            citizenships=["AU"],
            current_residency="AU",
            is_deleted=False,
        )
        deleted_client = Client(
            tenant_id=tenant_a.id,
            citizenships=["AU"],
            current_residency="AU",
            is_deleted=True,
        )
        other_tenant_client = Client(
            tenant_id=tenant_b.id,
            citizenships=["SG"],
            current_residency="SG",
            is_deleted=False,
        )
        db.add_all([active_client, deleted_client, other_tenant_client])
        db.flush()

        db.add_all(
            [
                Asset(
                    client_id=active_client.id,
                    type=AssetType.property,
                    location="AU",
                    ownership_structure=OwnershipStructure.individual,
                ),
                Asset(
                    client_id=deleted_client.id,
                    type=AssetType.cash,
                    location="AU",
                    ownership_structure=OwnershipStructure.individual,
                ),
                Asset(
                    client_id=other_tenant_client.id,
                    type=AssetType.company,
                    location="SG",
                    ownership_structure=OwnershipStructure.company,
                ),
            ]
        )
        db.commit()

        tenant_a_assets = list_assets(db, tenant_id=tenant_a.id)
        all_visible_assets = list_assets(db)

        assert [asset.client_id for asset in tenant_a_assets] == [active_client.id]
        assert {asset.client_id for asset in all_visible_assets} == {
            active_client.id,
            other_tenant_client.id,
        }


def test_clean_alembic_upgrade_creates_full_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "clean_migration.db"
    config = Config(str(ROOT_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    inspector = inspect(engine)

    assert {
        "assets",
        "clients",
        "knowledge_sources",
        "residency_history",
        "rules",
        "tenants",
    }.issubset(set(inspector.get_table_names()))

    rule_columns = {column["name"] for column in inspector.get_columns("rules")}
    assert "section_reference" in rule_columns


def test_ensure_schema_ready_requires_migrated_schema(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    monkeypatch.setattr(init_db_module, "engine", engine)

    with pytest.raises(RuntimeError, match="Database schema is not initialized"):
        init_db_module.ensure_schema_ready()


def test_frontend_api_calls_are_not_pinned_to_localhost():
    script = (ROOT_DIR / "script.js").read_text(encoding="utf-8")
    frontend_app = (ROOT_DIR / "frontend" / "app.js").read_text(encoding="utf-8")
    frontend_core = (ROOT_DIR / "frontend" / "core.js").read_text(encoding="utf-8")
    frontend_evaluation = (ROOT_DIR / "frontend" / "evaluation.js").read_text(encoding="utf-8")
    frontend_views = (ROOT_DIR / "frontend" / "evaluation_views.js").read_text(encoding="utf-8")
    index_html = (ROOT_DIR / "index.html").read_text(encoding="utf-8")

    assert 'await import("/frontend/app.js")' in script
    assert "Basic navigation is still available." in script
    assert "window.__clearPathNavInitialized" in script
    assert "127.0.0.1:8000" not in frontend_core
    assert "window.location.origin" in frontend_core
    assert "initEvaluationSection" in frontend_app
    assert "loadClients" not in frontend_app
    assert "evaluateGuidedSections" in index_html
    assert "advancedJsonToggle" in index_html
    assert "evaluateAssessmentLabel" in index_html
    assert "evaluationReviewPanel" in index_html
    assert "Export Local Copy" in index_html
    assert '"/evaluate/private"' in frontend_evaluation
    assert "parseAdvancedPayload" in frontend_evaluation
    assert "Assessment readiness" in frontend_evaluation
    assert "client_data: snapshot.payload" in frontend_evaluation
    assert "Custom JSON keys are preserved" in frontend_evaluation
    assert "renderEvaluationResult" in frontend_views
    assert "Apply JSON To Guided Form" in index_html
