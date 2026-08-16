"""add_organisation_currency

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-16 03:30:00.000000

Store billing currency on Organisation at signup (immutable thereafter).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organisations",
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="USD",
        ),
    )


def downgrade() -> None:
    op.drop_column("organisations", "currency")
