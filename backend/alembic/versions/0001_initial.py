"""Initial Alembic revision (no-op baseline).

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-09

We bootstrap the local schema from `backend/.sqls` (see scripts/dev_db_apply_sqls.sh),
then stamp Alembic to this revision. All future schema changes should be new Alembic
revisions after this baseline.
"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline: schema already exists.
    pass


def downgrade() -> None:
    raise NotImplementedError("Downgrades are not supported.")

