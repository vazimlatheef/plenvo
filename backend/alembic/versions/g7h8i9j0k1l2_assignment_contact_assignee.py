"""assignment_contact_assignee

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-21 17:00:00.000000

Allow training assignments to contacts without Plenvo user accounts.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    tables = set(insp.get_table_names())

    if "assignments" not in tables:
        op.create_table(
            "assignments",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("training_id", sa.BigInteger(), nullable=False),
            sa.Column("assignee_user_id", sa.BigInteger(), nullable=True),
            sa.Column("assignee_contact_id", sa.BigInteger(), nullable=True),
            sa.Column("assigned_by_id", sa.BigInteger(), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=20), server_default="not_started", nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("manager_notified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["assignee_contact_id"], ["contacts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["assigned_by_id"], ["users.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["training_id"], ["trainings.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("training_id", "assignee_contact_id", name="uq_assignments_training_contact"),
            sa.UniqueConstraint("training_id", "assignee_user_id", name="uq_assignments_training_user"),
        )
        op.create_index(op.f("ix_assignments_assignee_contact_id"), "assignments", ["assignee_contact_id"], unique=False)
        op.create_index(op.f("ix_assignments_assignee_user_id"), "assignments", ["assignee_user_id"], unique=False)
        op.create_index(op.f("ix_assignments_training_id"), "assignments", ["training_id"], unique=False)
        return

    cols = {c["name"] for c in insp.get_columns("assignments")}
    if "assignee_contact_id" not in cols:
        op.add_column("assignments", sa.Column("assignee_contact_id", sa.BigInteger(), nullable=True))
        op.create_index(op.f("ix_assignments_assignee_contact_id"), "assignments", ["assignee_contact_id"], unique=False)
        op.create_foreign_key(
            "fk_assignments_assignee_contact_id_contacts",
            "assignments",
            "contacts",
            ["assignee_contact_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.alter_column("assignments", "assignee_user_id", existing_type=sa.BigInteger(), nullable=True)

    constraints = {c["name"] for c in insp.get_unique_constraints("assignments")}
    if "uq_assignments_training_assignee" in constraints:
        op.drop_constraint("uq_assignments_training_assignee", "assignments", type_="unique")
    constraints = {c["name"] for c in inspect(bind).get_unique_constraints("assignments")}
    if "uq_assignments_training_user" not in constraints:
        op.create_unique_constraint("uq_assignments_training_user", "assignments", ["training_id", "assignee_user_id"])
    if "uq_assignments_training_contact" not in constraints:
        op.create_unique_constraint(
            "uq_assignments_training_contact", "assignments", ["training_id", "assignee_contact_id"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "assignments" not in insp.get_table_names():
        return

    cols = {c["name"] for c in insp.get_columns("assignments")}
    constraints = {c["name"] for c in insp.get_unique_constraints("assignments")}
    if "uq_assignments_training_contact" in constraints:
        op.drop_constraint("uq_assignments_training_contact", "assignments", type_="unique")
    if "uq_assignments_training_user" in constraints:
        op.drop_constraint("uq_assignments_training_user", "assignments", type_="unique")
    if "uq_assignments_training_assignee" not in constraints:
        op.create_unique_constraint("uq_assignments_training_assignee", "assignments", ["training_id", "assignee_user_id"])

    if "assignee_contact_id" in cols:
        op.drop_constraint("fk_assignments_assignee_contact_id_contacts", "assignments", type_="foreignkey")
        op.drop_index(op.f("ix_assignments_assignee_contact_id"), table_name="assignments")
        op.drop_column("assignments", "assignee_contact_id")

    op.alter_column("assignments", "assignee_user_id", existing_type=sa.BigInteger(), nullable=False)
