"""merge heads

Revision ID: 1c28e093d978
Revises: 239ee10c9fd1, h8i9j0k1l2m3
Create Date: 2026-08-22 01:26:02.406725

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c28e093d978'
down_revision: Union[str, Sequence[str], None] = ('239ee10c9fd1', 'h8i9j0k1l2m3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
