-- Billing subscription history table (one row per subscription_id)
-- Enables winner selection and replay-safe state reconstruction.
SET search_path = conthunt, public;

CREATE TABLE IF NOT EXISTS billing_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id TEXT NOT NULL UNIQUE,
    customer_id TEXT,
    product_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    last_webhook_ts TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_billing_subscriptions_user_id
    ON billing_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_subscriptions_status
    ON billing_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_billing_subscriptions_customer_id
    ON billing_subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_billing_subscriptions_last_webhook_ts
    ON billing_subscriptions(last_webhook_ts DESC);

-- Backfill from legacy pointer table (best effort).
INSERT INTO billing_subscriptions (
    user_id, subscription_id, customer_id, product_id, status,
    cancel_at_period_end, current_period_start, current_period_end,
    last_webhook_ts, created_at, updated_at
)
SELECT
    user_id, subscription_id, customer_id, product_id, status,
    cancel_at_period_end, current_period_start, current_period_end,
    COALESCE(last_webhook_ts, now()), created_at, updated_at
FROM user_subscriptions
ON CONFLICT (subscription_id) DO NOTHING;

-- RLS / permissions
ALTER TABLE billing_subscriptions ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON billing_subscriptions TO conthunt_app;
GRANT ALL ON billing_subscriptions TO conthunt_service;

DROP POLICY IF EXISTS billing_subscriptions_select_own ON billing_subscriptions;
CREATE POLICY billing_subscriptions_select_own
ON billing_subscriptions FOR SELECT TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS billing_subscriptions_service_all ON billing_subscriptions;
CREATE POLICY billing_subscriptions_service_all
ON billing_subscriptions FOR ALL TO conthunt_service
USING (true) WITH CHECK (true);
