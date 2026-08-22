"""task_project_links

Revision ID: i9j0k1l2m3n4
Revises: 1c28e093d978
Create Date: 2026-08-22 19:45:00.000000

Add optional JSON links arrays on tasks and projects.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, Sequence[str], None] = "1c28e093d978"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    task_cols = {c["name"] for c in insp.get_columns("tasks")}
    if "links" not in task_cols:
        op.add_column("tasks", sa.Column("links", sa.JSON(), nullable=True))

    project_cols = {c["name"] for c in insp.get_columns("projects")}
    if "links" not in project_cols:
        op.add_column("projects", sa.Column("links", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    task_cols = {c["name"] for c in insp.get_columns("tasks")}
    if "links" in task_cols:
        op.drop_column("tasks", "links")

    project_cols = {c["name"] for c in insp.get_columns("projects")}
    if "links" in project_cols:
        op.drop_column("projects", "links")
