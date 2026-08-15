"""add_contacts_and_task_assignee_contact

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-15 19:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    tables = set(insp.get_table_names())

    if "contacts" not in tables:
        op.create_table(
            "contacts",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("organisation_id", sa.BigInteger(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("role", sa.String(length=40), server_default="Member", nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=True),
            sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("organisation_id", "email", name="uq_contacts_org_email"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index(op.f("ix_contacts_email"), "contacts", ["email"], unique=False)
        op.create_index(op.f("ix_contacts_organisation_id"), "contacts", ["organisation_id"], unique=False)
        op.create_index(op.f("ix_contacts_user_id"), "contacts", ["user_id"], unique=True)

    task_cols = {c["name"] for c in insp.get_columns("tasks")}
    if "assignee_contact_id" not in task_cols:
        op.add_column("tasks", sa.Column("assignee_contact_id", sa.BigInteger(), nullable=True))
        op.create_index(op.f("ix_tasks_assignee_contact_id"), "tasks", ["assignee_contact_id"], unique=False)
        op.create_foreign_key(
            "fk_tasks_assignee_contact_id_contacts",
            "tasks",
            "contacts",
            ["assignee_contact_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    task_cols = {c["name"] for c in insp.get_columns("tasks")} if "tasks" in insp.get_table_names() else set()
    if "assignee_contact_id" in task_cols:
        op.drop_constraint("fk_tasks_assignee_contact_id_contacts", "tasks", type_="foreignkey")
        op.drop_index(op.f("ix_tasks_assignee_contact_id"), table_name="tasks")
        op.drop_column("tasks", "assignee_contact_id")

    if "contacts" in insp.get_table_names():
        op.drop_index(op.f("ix_contacts_user_id"), table_name="contacts")
        op.drop_index(op.f("ix_contacts_organisation_id"), table_name="contacts")
        op.drop_index(op.f("ix_contacts_email"), table_name="contacts")
        op.drop_table("contacts")
