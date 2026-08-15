"""add_user_email_preferences

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-15 19:20:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("users")}

    if "do_not_email" not in cols:
        op.add_column(
            "users",
            sa.Column("do_not_email", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        )
    if "email_unsubscribe_token" not in cols:
        op.add_column("users", sa.Column("email_unsubscribe_token", sa.String(length=64), nullable=True))
        op.create_index(
            op.f("ix_users_email_unsubscribe_token"),
            "users",
            ["email_unsubscribe_token"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("users")}

    if "email_unsubscribe_token" in cols:
        op.drop_index(op.f("ix_users_email_unsubscribe_token"), table_name="users")
        op.drop_column("users", "email_unsubscribe_token")
    if "do_not_email" in cols:
        op.drop_column("users", "do_not_email")
