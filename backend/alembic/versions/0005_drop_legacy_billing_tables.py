"""Drop legacy billing tables after migration to billing_* canonical state.

Revision ID: 0005_drop_legacy_billing_tables
Revises: 0004_billing_hardening_v1
Create Date: 2026-03-06
"""

from __future__ import annotations

import os

from alembic import op


revision = "0005_drop_legacy_billing_tables"
down_revision = "0004_billing_hardening_v1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        DROP TABLE IF EXISTS {schema}.pending_plan_changes CASCADE;
        DROP TABLE IF EXISTS {schema}.user_subscriptions CASCADE;
        DROP TABLE IF EXISTS {schema}.webhook_events CASCADE;
        """.strip()
    )


def downgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.pending_plan_changes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES {schema}.users(id) ON DELETE CASCADE,
            subscription_id TEXT NOT NULL,
            target_product_id TEXT NOT NULL,
            target_role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'applied', 'cancelled')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            applied_at TIMESTAMPTZ,
            cancelled_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS {schema}.user_subscriptions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES {schema}.users(id) ON DELETE CASCADE,
            subscription_id TEXT NOT NULL UNIQUE,
            customer_id TEXT,
            product_id TEXT NOT NULL,
            status TEXT NOT NULL,
            cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
            current_period_start TIMESTAMPTZ,
            current_period_end TIMESTAMPTZ,
            last_webhook_ts TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (user_id)
        );

        CREATE TABLE IF NOT EXISTS {schema}.webhook_events (
            webhook_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            subscription_id TEXT,
            payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """.strip()
    )
