"""trial_peak_member_count

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-08-27 18:15:00.000000

Track peak team headcount during trial for minimum-tier checkout enforcement.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "k1l2m3n4o5p6"
down_revision: Union[str, Sequence[str], None] = "j0k1l2m3n4o5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    org_cols = {c["name"] for c in insp.get_columns("organisations")}
    if "trial_peak_member_count" not in org_cols:
        op.add_column(
            "organisations",
            sa.Column("trial_peak_member_count", sa.Integer(), nullable=False, server_default="1"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "organisations" not in insp.get_table_names():
        return
    org_cols = {c["name"] for c in insp.get_columns("organisations")}
    if "trial_peak_member_count" in org_cols:
        op.drop_column("organisations", "trial_peak_member_count")
