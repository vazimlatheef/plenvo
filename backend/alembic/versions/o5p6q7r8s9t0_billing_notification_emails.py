"""billing notification timestamps

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-08-31 20:55:00.000000

Track paid-welcome and cancel-notice emails so webhooks do not double-send.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "o5p6q7r8s9t0"
down_revision: Union[str, Sequence[str], None] = "n4o5p6q7r8s9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("organisations")}
    if "paid_welcome_email_sent_at" not in cols:
        op.add_column(
            "organisations",
            sa.Column("paid_welcome_email_sent_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "cancel_notice_email_sent_at" not in cols:
        op.add_column(
            "organisations",
            sa.Column("cancel_notice_email_sent_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("organisations")}
    if "cancel_notice_email_sent_at" in cols:
        op.drop_column("organisations", "cancel_notice_email_sent_at")
    if "paid_welcome_email_sent_at" in cols:
        op.drop_column("organisations", "paid_welcome_email_sent_at")
