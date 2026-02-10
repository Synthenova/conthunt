"""Smoketest: drop the disposable table (keeps migration history).

Revision ID: 0003_smoketest_drop_table
Revises: 0002_smoketest_create_table
Create Date: 2026-02-09
"""

from __future__ import annotations

import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_smoketest_drop_table"
down_revision = "0002_smoketest_create_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(f"DROP TABLE IF EXISTS {schema}._alembic_smoketest;")


def downgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}._alembic_smoketest (
            id BIGSERIAL PRIMARY KEY,
            note TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """.strip()
    )

