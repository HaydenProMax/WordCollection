"""add lookup language direction

Revision ID: 20260510_0002
Revises: 20260510_0001
Create Date: 2026-05-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260510_0002"
down_revision: Union[str, None] = "20260510_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "lookups",
        sa.Column("source_language", sa.String(length=16), server_default="en", nullable=False),
    )
    op.add_column(
        "lookups",
        sa.Column("target_language", sa.String(length=16), server_default="zh", nullable=False),
    )
    op.alter_column("lookups", "source_language", server_default=None)
    op.alter_column("lookups", "target_language", server_default=None)


def downgrade() -> None:
    op.drop_column("lookups", "target_language")
    op.drop_column("lookups", "source_language")
