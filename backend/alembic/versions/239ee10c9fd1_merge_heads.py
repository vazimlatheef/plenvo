"""merge heads

Revision ID: 239ee10c9fd1
Revises: a8b9c0d1e2f3, g7h8i9j0k1l2
Create Date: 2026-08-21 17:53:47.633836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '239ee10c9fd1'
down_revision: Union[str, Sequence[str], None] = ('a8b9c0d1e2f3', 'g7h8i9j0k1l2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
