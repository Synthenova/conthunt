"""Persist trial facts on billing subscriptions for DB-backed entitlement checks.

Revision ID: 0008_add_trial_fields_to_billing_subscriptions
Revises: 0007_remove_free_plan_entitlements
Create Date: 2026-04-11
"""

from __future__ import annotations

import os

from alembic import op


revision = "0008_add_trial_fields_to_billing_subscriptions"
down_revision = "0007_remove_free_plan_entitlements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        ALTER TABLE {schema}.billing_subscriptions
        ADD COLUMN IF NOT EXISTS trial_period_days INTEGER,
        ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS first_charge_at TIMESTAMPTZ;
        """.strip()
    )


def downgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        ALTER TABLE {schema}.billing_subscriptions
        DROP COLUMN IF EXISTS first_charge_at,
        DROP COLUMN IF EXISTS trial_ends_at,
        DROP COLUMN IF EXISTS trial_period_days;
        """.strip()
    )
