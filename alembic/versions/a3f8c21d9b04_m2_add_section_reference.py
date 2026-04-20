"""m2_add_section_reference

Revision ID: a3f8c21d9b04
Revises: 125257ea7788
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f8c21d9b04"
down_revision: Union[str, None] = "125257ea7788"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("rules", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("section_reference", sa.String(200), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("rules", schema=None) as batch_op:
        batch_op.drop_column("section_reference")
