"""profile role division address

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-08-27 19:00:00.000000

Add team_division and address on users; role_other and team_division on contacts.
Migrate legacy contact role labels to professional roles.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "l2m3n4o5p6q7"
down_revision: Union[str, Sequence[str], None] = "k1l2m3n4o5p6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "team_division" not in user_cols:
        op.add_column("users", sa.Column("team_division", sa.String(length=200), nullable=True))
    if "address" not in user_cols:
        op.add_column("users", sa.Column("address", sa.String(length=500), nullable=True))

    if "contacts" in insp.get_table_names():
        contact_cols = {c["name"] for c in insp.get_columns("contacts")}
        if "role_other" not in contact_cols:
            op.add_column("contacts", sa.Column("role_other", sa.String(length=200), nullable=True))
        if "team_division" not in contact_cols:
            op.add_column("contacts", sa.Column("team_division", sa.String(length=200), nullable=True))

        op.execute("UPDATE contacts SET role = 'Team Member' WHERE role = 'Member'")
        op.execute("UPDATE contacts SET role = 'Individual Contributor' WHERE role = 'Contractor'")
        op.execute(
            "UPDATE contacts SET role = 'Other', role_other = COALESCE(role_other, 'Client') WHERE role = 'Client'"
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "address" in user_cols:
        op.drop_column("users", "address")
    if "team_division" in user_cols:
        op.drop_column("users", "team_division")

    if "contacts" in insp.get_table_names():
        contact_cols = {c["name"] for c in insp.get_columns("contacts")}
        if "team_division" in contact_cols:
            op.drop_column("contacts", "team_division")
        if "role_other" in contact_cols:
            op.drop_column("contacts", "role_other")
