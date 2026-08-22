"""overdue_email_notifications

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-08-22 01:30:00.000000

Overdue task email opt-in on users; per-task overdue_notified_at to avoid duplicate alerts.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, Sequence[str], None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "overdue_email_enabled" not in user_cols:
        op.add_column(
            "users",
            sa.Column("overdue_email_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )

    task_cols = {c["name"] for c in insp.get_columns("tasks")}
    if "overdue_notified_at" not in task_cols:
        op.add_column("tasks", sa.Column("overdue_notified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    task_cols = {c["name"] for c in insp.get_columns("tasks")} if "tasks" in insp.get_table_names() else set()
    if "overdue_notified_at" in task_cols:
        op.drop_column("tasks", "overdue_notified_at")

    user_cols = {c["name"] for c in insp.get_columns("users")} if "users" in insp.get_table_names() else set()
    if "overdue_email_enabled" in user_cols:
        op.drop_column("users", "overdue_email_enabled")
