"""task recurrence series

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-08-31 20:10:00.000000

Weekly/monthly repeating tasks: recurrence + series_id.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "n4o5p6q7r8s9"
down_revision: Union[str, Sequence[str], None] = "m3n4o5p6q7r8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("tasks")}
    if "recurrence" not in cols:
        op.add_column(
            "tasks",
            sa.Column("recurrence", sa.String(length=20), nullable=False, server_default="none"),
        )
    if "series_id" not in cols:
        op.add_column("tasks", sa.Column("series_id", sa.String(length=36), nullable=True))
        op.create_index("ix_tasks_series_id", "tasks", ["series_id"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("tasks")}
    indexes = {i["name"] for i in insp.get_indexes("tasks")}
    if "ix_tasks_series_id" in indexes:
        op.drop_index("ix_tasks_series_id", table_name="tasks")
    if "series_id" in cols:
        op.drop_column("tasks", "series_id")
    if "recurrence" in cols:
        op.drop_column("tasks", "recurrence")
