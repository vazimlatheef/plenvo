"""initial_schema — baseline matching current SQLAlchemy models.

Revision ID: d0da0a6888ff
Revises:
Create Date: 2026-08-15 18:10:05.024281

Autogenerate against an already-synced DB produced an empty revision.
This baseline uses metadata.create_all (checkfirst=True) so:
  - fresh databases get the full schema
  - existing databases are left intact when upgrading to this revision
"""

from typing import Sequence, Union

from alembic import op

from app.models import Base

# revision identifiers, used by Alembic.
revision: str = "d0da0a6888ff"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
