"""m3_add_review_status

Revision ID: b7e4f12c3a01
Revises: a3f8c21d9b04
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7e4f12c3a01"
down_revision: Union[str, None] = "a3f8c21d9b04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("rules", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "review_status",
                sa.Enum("verified_current", "needs_update", "unsupported_or_wrong_source", name="reviewstatus"),
                nullable=False,
                server_default="verified_current",
            )
        )
        batch_op.create_index("ix_rules_review_status", ["review_status"])


def downgrade() -> None:
    with op.batch_alter_table("rules", schema=None) as batch_op:
        batch_op.drop_index("ix_rules_review_status")
        batch_op.drop_column("review_status")
