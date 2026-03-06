"""Billing hardening foundation tables and explicit state columns.

Revision ID: 0004_billing_hardening_v1
Revises: 0003_smoketest_drop_table
Create Date: 2026-03-06
"""

from __future__ import annotations

import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_billing_hardening_v1"
down_revision = "0003_smoketest_drop_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        SET search_path TO {schema}, public;

        CREATE TABLE IF NOT EXISTS {schema}.billing_customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES {schema}.users(id) ON DELETE CASCADE,
            provider TEXT NOT NULL DEFAULT 'dodo',
            provider_customer_id TEXT NOT NULL,
            email TEXT,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'inactive', 'merged')),
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (provider, provider_customer_id),
            UNIQUE (user_id, provider)
        );

        CREATE INDEX IF NOT EXISTS idx_billing_customers_user_id
            ON {schema}.billing_customers(user_id);

        CREATE TABLE IF NOT EXISTS {schema}.billing_operations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES {schema}.users(id) ON DELETE CASCADE,
            provider TEXT NOT NULL DEFAULT 'dodo',
            operation_type TEXT NOT NULL
                CHECK (
                    operation_type IN (
                        'checkout_start',
                        'checkout_complete',
                        'checkout_fail',
                        'upgrade_request',
                        'upgrade_apply',
                        'upgrade_fail',
                        'downgrade_schedule',
                        'downgrade_apply',
                        'downgrade_cancel',
                        'cancel_schedule',
                        'cancel_undo',
                        'reactivation_start',
                        'reactivation_complete',
                        'reactivation_fail',
                        'sync_reconcile'
                    )
                ),
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
            ui_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (
                    ui_status IN (
                        'pending',
                        'awaiting_webhook',
                        'requires_action',
                        'completed',
                        'failed',
                        'cancelled'
                    )
                ),
            provider_subscription_id TEXT,
            provider_customer_id TEXT,
            requested_from_product_id TEXT,
            requested_to_product_id TEXT,
            result_product_id TEXT,
            idempotency_key TEXT,
            failure_code TEXT,
            failure_reason TEXT,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_billing_operations_user_id
            ON {schema}.billing_operations(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_billing_operations_subscription
            ON {schema}.billing_operations(provider_subscription_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_billing_operations_pending
            ON {schema}.billing_operations(user_id, operation_type, created_at DESC)
            WHERE status = 'pending';
        CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_operations_idempotency
            ON {schema}.billing_operations(provider, idempotency_key)
            WHERE idempotency_key IS NOT NULL;

        CREATE TABLE IF NOT EXISTS {schema}.billing_payments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            provider TEXT NOT NULL DEFAULT 'dodo',
            provider_payment_id TEXT NOT NULL,
            provider_subscription_id TEXT,
            operation_id UUID REFERENCES {schema}.billing_operations(id) ON DELETE SET NULL,
            payment_type TEXT NOT NULL DEFAULT 'subscription'
                CHECK (
                    payment_type IN (
                        'checkout',
                        'subscription',
                        'upgrade_proration',
                        'renewal',
                        'reactivation',
                        'manual'
                    )
                ),
            status TEXT NOT NULL
                CHECK (
                    status IN (
                        'pending',
                        'processing',
                        'paid',
                        'failed',
                        'cancelled',
                        'refunded',
                        'requires_action'
                    )
                ),
            amount INTEGER NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'USD',
            failure_code TEXT,
            failure_message TEXT,
            paid_at TIMESTAMPTZ,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (provider, provider_payment_id)
        );

        CREATE INDEX IF NOT EXISTS idx_billing_payments_subscription
            ON {schema}.billing_payments(provider_subscription_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_billing_payments_operation
            ON {schema}.billing_payments(operation_id);
        CREATE INDEX IF NOT EXISTS idx_billing_payments_status
            ON {schema}.billing_payments(status, created_at DESC);

        CREATE TABLE IF NOT EXISTS {schema}.billing_webhook_inbox (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            provider TEXT NOT NULL DEFAULT 'dodo',
            webhook_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_ts TIMESTAMPTZ,
            provider_subscription_id TEXT,
            payload JSONB NOT NULL,
            processing_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (processing_status IN ('pending', 'processed', 'failed', 'skipped')),
            error_message TEXT,
            received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            processed_at TIMESTAMPTZ,
            UNIQUE (provider, webhook_id)
        );

        CREATE INDEX IF NOT EXISTS idx_billing_webhook_inbox_subscription
            ON {schema}.billing_webhook_inbox(provider_subscription_id, received_at DESC);
        CREATE INDEX IF NOT EXISTS idx_billing_webhook_inbox_status
            ON {schema}.billing_webhook_inbox(processing_status, received_at DESC);

        CREATE TABLE IF NOT EXISTS {schema}.billing_audit_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES {schema}.users(id) ON DELETE CASCADE,
            provider TEXT NOT NULL DEFAULT 'dodo',
            provider_subscription_id TEXT,
            operation_id UUID REFERENCES {schema}.billing_operations(id) ON DELETE SET NULL,
            event_name TEXT NOT NULL,
            payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_billing_audit_log_user_id
            ON {schema}.billing_audit_log(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_billing_audit_log_subscription
            ON {schema}.billing_audit_log(provider_subscription_id, created_at DESC);

        ALTER TABLE {schema}.billing_subscriptions
            ADD COLUMN IF NOT EXISTS provider TEXT NOT NULL DEFAULT 'dodo',
            ADD COLUMN IF NOT EXISTS effective_product_id TEXT,
            ADD COLUMN IF NOT EXISTS billing_state TEXT NOT NULL DEFAULT 'none'
                CHECK (
                    billing_state IN (
                        'none',
                        'pending_activation',
                        'active',
                        'active_cancel_scheduled',
                        'on_hold',
                        'cancelled',
                        'expired',
                        'failed'
                    )
                ),
            ADD COLUMN IF NOT EXISTS payment_status TEXT NOT NULL DEFAULT 'none'
                CHECK (
                    payment_status IN (
                        'none',
                        'pending',
                        'processing',
                        'paid',
                        'failed',
                        'cancelled',
                        'refunded',
                        'requires_action'
                    )
                ),
            ADD COLUMN IF NOT EXISTS access_status TEXT NOT NULL DEFAULT 'none'
                CHECK (
                    access_status IN (
                        'none',
                        'active',
                        'grace',
                        'restricted',
                        'suspended',
                        'ended'
                    )
                ),
            ADD COLUMN IF NOT EXISTS entitlement_status TEXT NOT NULL DEFAULT 'none'
                CHECK (
                    entitlement_status IN (
                        'none',
                        'effective',
                        'pending_change',
                        'restricted',
                        'ended'
                    )
                ),
            ADD COLUMN IF NOT EXISTS pending_change_type TEXT
                CHECK (pending_change_type IN ('upgrade', 'downgrade', 'cancel', 'reactivation')),
            ADD COLUMN IF NOT EXISTS pending_target_product_id TEXT,
            ADD COLUMN IF NOT EXISTS pending_effective_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS last_payment_status TEXT
                CHECK (
                    last_payment_status IN (
                        'none',
                        'pending',
                        'processing',
                        'paid',
                        'failed',
                        'cancelled',
                        'refunded',
                        'requires_action'
                    )
                ),
            ADD COLUMN IF NOT EXISTS last_paid_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb;

        UPDATE {schema}.billing_subscriptions
        SET
            effective_product_id = COALESCE(effective_product_id, product_id),
            billing_state = CASE
                WHEN status = 'active' AND cancel_at_period_end THEN 'active_cancel_scheduled'
                WHEN status = 'active' THEN 'active'
                WHEN status = 'on_hold' THEN 'on_hold'
                WHEN status = 'cancelled' THEN 'cancelled'
                WHEN status = 'expired' THEN 'expired'
                WHEN status = 'failed' THEN 'failed'
                WHEN status = 'pending' THEN 'pending_activation'
                ELSE billing_state
            END,
            payment_status = CASE
                WHEN status = 'active' THEN 'paid'
                WHEN status = 'on_hold' THEN 'failed'
                WHEN status = 'pending' THEN 'pending'
                ELSE payment_status
            END,
            access_status = CASE
                WHEN status = 'active' THEN 'active'
                WHEN status = 'on_hold' THEN 'restricted'
                WHEN status = 'cancelled'
                     AND current_period_end IS NOT NULL
                     AND current_period_end > now() THEN 'grace'
                WHEN status IN ('cancelled', 'expired', 'failed') THEN 'ended'
                ELSE access_status
            END,
            entitlement_status = CASE
                WHEN status = 'active' THEN 'effective'
                WHEN status = 'on_hold' THEN 'restricted'
                WHEN status IN ('cancelled', 'expired', 'failed') THEN 'ended'
                ELSE entitlement_status
            END,
            last_payment_status = COALESCE(last_payment_status, CASE
                WHEN status = 'active' THEN 'paid'
                WHEN status = 'on_hold' THEN 'failed'
                WHEN status = 'pending' THEN 'pending'
                ELSE 'none'
            END);

        CREATE INDEX IF NOT EXISTS idx_billing_subscriptions_billing_state
            ON {schema}.billing_subscriptions(billing_state);
        CREATE INDEX IF NOT EXISTS idx_billing_subscriptions_payment_status
            ON {schema}.billing_subscriptions(payment_status);
        CREATE INDEX IF NOT EXISTS idx_billing_subscriptions_effective_product
            ON {schema}.billing_subscriptions(effective_product_id);

        ALTER TABLE {schema}.billing_customers ENABLE ROW LEVEL SECURITY;
        GRANT SELECT ON {schema}.billing_customers TO conthunt_app;
        GRANT ALL ON {schema}.billing_customers TO conthunt_service;
        DROP POLICY IF EXISTS billing_customers_select_own ON {schema}.billing_customers;
        CREATE POLICY billing_customers_select_own
            ON {schema}.billing_customers FOR SELECT TO conthunt_app
            USING (user_id = current_setting('app.user_id', true)::uuid);
        DROP POLICY IF EXISTS billing_customers_service_all ON {schema}.billing_customers;
        CREATE POLICY billing_customers_service_all
            ON {schema}.billing_customers FOR ALL TO conthunt_service
            USING (true) WITH CHECK (true);

        ALTER TABLE {schema}.billing_operations ENABLE ROW LEVEL SECURITY;
        GRANT SELECT ON {schema}.billing_operations TO conthunt_app;
        GRANT ALL ON {schema}.billing_operations TO conthunt_service;
        DROP POLICY IF EXISTS billing_operations_select_own ON {schema}.billing_operations;
        CREATE POLICY billing_operations_select_own
            ON {schema}.billing_operations FOR SELECT TO conthunt_app
            USING (user_id = current_setting('app.user_id', true)::uuid);
        DROP POLICY IF EXISTS billing_operations_service_all ON {schema}.billing_operations;
        CREATE POLICY billing_operations_service_all
            ON {schema}.billing_operations FOR ALL TO conthunt_service
            USING (true) WITH CHECK (true);

        ALTER TABLE {schema}.billing_payments ENABLE ROW LEVEL SECURITY;
        GRANT SELECT ON {schema}.billing_payments TO conthunt_app;
        GRANT ALL ON {schema}.billing_payments TO conthunt_service;
        DROP POLICY IF EXISTS billing_payments_select_own ON {schema}.billing_payments;
        CREATE POLICY billing_payments_select_own
            ON {schema}.billing_payments FOR SELECT TO conthunt_app
            USING (
                provider_subscription_id IN (
                    SELECT subscription_id
                    FROM {schema}.billing_subscriptions
                    WHERE user_id = current_setting('app.user_id', true)::uuid
                )
            );
        DROP POLICY IF EXISTS billing_payments_service_all ON {schema}.billing_payments;
        CREATE POLICY billing_payments_service_all
            ON {schema}.billing_payments FOR ALL TO conthunt_service
            USING (true) WITH CHECK (true);

        ALTER TABLE {schema}.billing_webhook_inbox ENABLE ROW LEVEL SECURITY;
        GRANT ALL ON {schema}.billing_webhook_inbox TO conthunt_service;
        DROP POLICY IF EXISTS billing_webhook_inbox_service_all ON {schema}.billing_webhook_inbox;
        CREATE POLICY billing_webhook_inbox_service_all
            ON {schema}.billing_webhook_inbox FOR ALL TO conthunt_service
            USING (true) WITH CHECK (true);

        ALTER TABLE {schema}.billing_audit_log ENABLE ROW LEVEL SECURITY;
        GRANT SELECT ON {schema}.billing_audit_log TO conthunt_app;
        GRANT ALL ON {schema}.billing_audit_log TO conthunt_service;
        DROP POLICY IF EXISTS billing_audit_log_select_own ON {schema}.billing_audit_log;
        CREATE POLICY billing_audit_log_select_own
            ON {schema}.billing_audit_log FOR SELECT TO conthunt_app
            USING (
                user_id = current_setting('app.user_id', true)::uuid
                OR (
                    user_id IS NULL
                    AND provider_subscription_id IN (
                        SELECT subscription_id
                        FROM {schema}.billing_subscriptions
                        WHERE user_id = current_setting('app.user_id', true)::uuid
                    )
                )
            );
        DROP POLICY IF EXISTS billing_audit_log_service_all ON {schema}.billing_audit_log;
        CREATE POLICY billing_audit_log_service_all
            ON {schema}.billing_audit_log FOR ALL TO conthunt_service
            USING (true) WITH CHECK (true);
        """.strip()
    )


def downgrade() -> None:
    raise NotImplementedError("Downgrades are not supported.")
