"""Initial schema — Postgres dedicado."""

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # create_all via init_db handles fresh installs; migration for explicit PG deploy
    pass


def downgrade() -> None:
    pass
