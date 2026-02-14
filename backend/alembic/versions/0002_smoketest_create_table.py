"""Smoketest: create a disposable table.

Revision ID: 0002_smoketest_create_table
Revises: 0001_initial
Create Date: 2026-02-09
"""

from __future__ import annotations

import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_smoketest_create_table"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
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


def downgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(f"DROP TABLE IF EXISTS {schema}._alembic_smoketest;")

