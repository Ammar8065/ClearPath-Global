"""initial schema

Revision ID: 125257ea7788
Revises: 
Create Date: 2026-03-22 12:22:37.741375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '125257ea7788'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jurisdiction", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum(
                "government_guidance",
                "legislation",
                "guidance",
                "treaty",
                "commentary",
                name="sourcetype",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(op.f("ix_knowledge_sources_id"), "knowledge_sources", ["id"], unique=False)
    op.create_index(
        op.f("ix_knowledge_sources_jurisdiction"),
        "knowledge_sources",
        ["jurisdiction"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_sources_source_type"),
        "knowledge_sources",
        ["source_type"],
        unique=False,
    )

    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_tenants_id"), "tenants", ["id"], unique=False)
    op.create_index(op.f("ix_tenants_name"), "tenants", ["name"], unique=False)

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("citizenships", sa.JSON(), nullable=False),
        sa.Column("current_residency", sa.String(length=100), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clients_current_residency"), "clients", ["current_residency"], unique=False)
    op.create_index(op.f("ix_clients_id"), "clients", ["id"], unique=False)
    op.create_index(op.f("ix_clients_is_deleted"), "clients", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_clients_tenant_id"), "clients", ["tenant_id"], unique=False)

    op.create_table(
        "rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_code", sa.String(length=100), nullable=False),
        sa.Column("jurisdiction", sa.String(length=100), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "residency",
                "tax",
                "cross_border",
                "structure",
                name="rulecategory",
            ),
            nullable=False,
        ),
        sa.Column("condition_expression", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "risk_level",
            sa.Enum("low", "medium", "high", name="risklevel"),
            nullable=False,
        ),
        sa.Column(
            "confidence_level",
            sa.Enum("low", "medium", "high", name="confidencelevel"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["knowledge_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_code", "version", name="uq_rule_code_version"),
    )
    op.create_index(op.f("ix_rules_category"), "rules", ["category"], unique=False)
    op.create_index(op.f("ix_rules_confidence_level"), "rules", ["confidence_level"], unique=False)
    op.create_index(op.f("ix_rules_effective_from"), "rules", ["effective_from"], unique=False)
    op.create_index(op.f("ix_rules_id"), "rules", ["id"], unique=False)
    op.create_index(op.f("ix_rules_is_deleted"), "rules", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_rules_jurisdiction"), "rules", ["jurisdiction"], unique=False)
    op.create_index(op.f("ix_rules_risk_level"), "rules", ["risk_level"], unique=False)
    op.create_index(op.f("ix_rules_rule_code"), "rules", ["rule_code"], unique=False)
    op.create_index(op.f("ix_rules_source_id"), "rules", ["source_id"], unique=False)
    op.create_index(op.f("ix_rules_version"), "rules", ["version"], unique=False)

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("property", "company", "cash", "investment", name="assettype"),
            nullable=False,
        ),
        sa.Column("location", sa.String(length=100), nullable=False),
        sa.Column(
            "ownership_structure",
            sa.Enum("individual", "trust", "company", name="ownershipstructure"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assets_client_id"), "assets", ["client_id"], unique=False)
    op.create_index(op.f("ix_assets_id"), "assets", ["id"], unique=False)
    op.create_index(op.f("ix_assets_location"), "assets", ["location"], unique=False)
    op.create_index(op.f("ix_assets_ownership_structure"), "assets", ["ownership_structure"], unique=False)
    op.create_index(op.f("ix_assets_type"), "assets", ["type"], unique=False)

    op.create_table(
        "residency_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_residency_history_client_id"), "residency_history", ["client_id"], unique=False)
    op.create_index(op.f("ix_residency_history_country"), "residency_history", ["country"], unique=False)
    op.create_index(op.f("ix_residency_history_id"), "residency_history", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_residency_history_id"), table_name="residency_history")
    op.drop_index(op.f("ix_residency_history_country"), table_name="residency_history")
    op.drop_index(op.f("ix_residency_history_client_id"), table_name="residency_history")
    op.drop_table("residency_history")

    op.drop_index(op.f("ix_assets_type"), table_name="assets")
    op.drop_index(op.f("ix_assets_ownership_structure"), table_name="assets")
    op.drop_index(op.f("ix_assets_location"), table_name="assets")
    op.drop_index(op.f("ix_assets_id"), table_name="assets")
    op.drop_index(op.f("ix_assets_client_id"), table_name="assets")
    op.drop_table("assets")

    op.drop_index(op.f("ix_rules_version"), table_name="rules")
    op.drop_index(op.f("ix_rules_source_id"), table_name="rules")
    op.drop_index(op.f("ix_rules_rule_code"), table_name="rules")
    op.drop_index(op.f("ix_rules_risk_level"), table_name="rules")
    op.drop_index(op.f("ix_rules_jurisdiction"), table_name="rules")
    op.drop_index(op.f("ix_rules_is_deleted"), table_name="rules")
    op.drop_index(op.f("ix_rules_id"), table_name="rules")
    op.drop_index(op.f("ix_rules_effective_from"), table_name="rules")
    op.drop_index(op.f("ix_rules_confidence_level"), table_name="rules")
    op.drop_index(op.f("ix_rules_category"), table_name="rules")
    op.drop_table("rules")

    op.drop_index(op.f("ix_clients_tenant_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_is_deleted"), table_name="clients")
    op.drop_index(op.f("ix_clients_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_current_residency"), table_name="clients")
    op.drop_table("clients")

    op.drop_index(op.f("ix_tenants_name"), table_name="tenants")
    op.drop_index(op.f("ix_tenants_id"), table_name="tenants")
    op.drop_table("tenants")

    op.drop_index(op.f("ix_knowledge_sources_source_type"), table_name="knowledge_sources")
    op.drop_index(op.f("ix_knowledge_sources_jurisdiction"), table_name="knowledge_sources")
    op.drop_index(op.f("ix_knowledge_sources_id"), table_name="knowledge_sources")
    op.drop_table("knowledge_sources")
