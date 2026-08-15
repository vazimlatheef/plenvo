"""backfill_user_first_last_name_split

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-15 23:20:00.000000

Users already have first_name / last_name columns. This migration backfills rows where
the full name was stored in first_name (empty last_name) by splitting on the first space,
falling back to the email local-part when first_name is empty.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _split_name(full: str, email: str) -> tuple[str, str]:
    text = (full or "").strip()
    if not text:
        local = (email or "").split("@", 1)[0].strip() or "User"
        # jane.doe / jane_doe → Jane
        token = local.replace(".", " ").replace("_", " ").replace("-", " ").split()[0]
        return token[:1].upper() + token[1:] if token else "User", ""
    parts = text.split(None, 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, email, first_name, last_name FROM users")
    ).mappings().all()

    for row in rows:
        first = (row["first_name"] or "").strip()
        last = (row["last_name"] or "").strip()
        email = row["email"] or ""

        # Already has a real last name — leave alone.
        if last:
            continue

        # Empty first name, or first name looks like a full name (contains a space).
        if (not first) or (" " in first):
            new_first, new_last = _split_name(first, email)
            conn.execute(
                sa.text(
                    "UPDATE users SET first_name = :fn, last_name = :ln WHERE id = :id"
                ),
                {"fn": new_first, "ln": new_last, "id": row["id"]},
            )


def downgrade() -> None:
    # Irreversible data backfill.
    pass
