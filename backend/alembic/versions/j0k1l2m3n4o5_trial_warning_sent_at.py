"""trial_warning_sent_at

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-08-23 01:50:00.000000

Track one trial-ending warning email per organisation trial.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, Sequence[str], None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    org_cols = {c["name"] for c in insp.get_columns("organisations")}
    if "trial_warning_sent_at" not in org_cols:
        op.add_column(
            "organisations",
            sa.Column("trial_warning_sent_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "organisations" not in insp.get_table_names():
        return
    org_cols = {c["name"] for c in insp.get_columns("organisations")}
    if "trial_warning_sent_at" in org_cols:
        op.drop_column("organisations", "trial_warning_sent_at")
