"""add_profile_and_contact_professional_fields

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-15 22:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    user_cols = {c["name"]: c for c in insp.get_columns("users")}
    if "phone_number" in user_cols:
        # Widen for international formatting.
        op.alter_column(
            "users",
            "phone_number",
            existing_type=sa.String(length=32),
            type_=sa.String(length=64),
            existing_nullable=True,
        )

    contact_cols = {c["name"] for c in insp.get_columns("contacts")} if "contacts" in insp.get_table_names() else set()
    if "company" not in contact_cols:
        op.add_column("contacts", sa.Column("company", sa.String(length=200), nullable=True))
    if "phone" not in contact_cols:
        op.add_column("contacts", sa.Column("phone", sa.String(length=64), nullable=True))
    if "linkedin_url" not in contact_cols:
        op.add_column("contacts", sa.Column("linkedin_url", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    contact_cols = {c["name"] for c in insp.get_columns("contacts")} if "contacts" in insp.get_table_names() else set()

    if "linkedin_url" in contact_cols:
        op.drop_column("contacts", "linkedin_url")
    if "phone" in contact_cols:
        op.drop_column("contacts", "phone")
    if "company" in contact_cols:
        op.drop_column("contacts", "company")

    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "phone_number" in user_cols:
        op.alter_column(
            "users",
            "phone_number",
            existing_type=sa.String(length=64),
            type_=sa.String(length=32),
            existing_nullable=True,
        )
