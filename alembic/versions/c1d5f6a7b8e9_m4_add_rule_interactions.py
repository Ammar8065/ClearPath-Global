"""m4_add_rule_interactions

Revision ID: c1d5f6a7b8e9
Revises: b7e4f12c3a01
Create Date: 2026-07-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1d5f6a7b8e9"
down_revision: Union[str, None] = "b7e4f12c3a01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rule_interactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("primary_rule_code", sa.String(length=100), nullable=False),
        sa.Column("related_rule_code", sa.String(length=100), nullable=False),
        sa.Column(
            "interaction_type",
            sa.Enum("relief", "exception", name="interactiontype"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("primary_rule_code", "related_rule_code", name="uq_rule_interaction_pair"),
    )
    op.create_index("ix_rule_interactions_primary_rule_code", "rule_interactions", ["primary_rule_code"])
    op.create_index("ix_rule_interactions_related_rule_code", "rule_interactions", ["related_rule_code"])
    op.create_index("ix_rule_interactions_interaction_type", "rule_interactions", ["interaction_type"])


def downgrade() -> None:
    op.drop_index("ix_rule_interactions_interaction_type", table_name="rule_interactions")
    op.drop_index("ix_rule_interactions_related_rule_code", table_name="rule_interactions")
    op.drop_index("ix_rule_interactions_primary_rule_code", table_name="rule_interactions")
    op.drop_table("rule_interactions")
