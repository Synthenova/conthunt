-- Dodo Billing System Migration
-- Creates tables for subscription management, pending plan changes, and webhook idempotency
SET search_path = conthunt, public;

-- ============================================================================
-- 1. USER_SUBSCRIPTIONS: Source of truth synced from Dodo webhooks
-- ============================================================================
-- One row per user. Updated on every subscription webhook.
-- Uses last_webhook_ts for out-of-order event protection.

CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    subscription_id TEXT NOT NULL UNIQUE,
    customer_id TEXT,
    product_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- active, on_hold, cancelled, expired, pending
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    last_webhook_ts TIMESTAMPTZ NOT NULL, -- For out-of-order protection
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_subscription_id ON user_subscriptions(subscription_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);

-- ============================================================================
-- 2. PENDING_PLAN_CHANGES: Local queue for downgrades at end of cycle
-- ============================================================================
-- Dodo applies plan changes immediately. We queue downgrades here and apply
-- them when subscription.renewed webhook fires.

CREATE TABLE IF NOT EXISTS pending_plan_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id TEXT NOT NULL,
    target_product_id TEXT NOT NULL,
    target_role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'applied', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    applied_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pending_plan_changes_user_id ON pending_plan_changes(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_plan_changes_status ON pending_plan_changes(status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_pending_plan_changes_subscription ON pending_plan_changes(subscription_id);

-- ============================================================================
-- 3. WEBHOOK_EVENTS: Idempotent webhook processing
-- ============================================================================
-- Primary key on webhook_id prevents double-processing of the same event.

CREATE TABLE IF NOT EXISTS webhook_events (
    webhook_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    subscription_id TEXT,
    payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_subscription ON webhook_events(subscription_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON webhook_events(processed_at DESC);

-- ============================================================================
-- 4. USERS: Add billing columns
-- ============================================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS dodo_customer_id TEXT;
CREATE INDEX IF NOT EXISTS idx_users_dodo_customer ON users(dodo_customer_id);

-- credit_period_start: For monthly credit resets (advances every 30 days)
-- Separate from billing cycle - yearly plans still get monthly credit limits
ALTER TABLE users ADD COLUMN IF NOT EXISTS credit_period_start TIMESTAMPTZ;

-- ============================================================================
-- 5. RLS & PERMISSIONS
-- ============================================================================

-- user_subscriptions: Users can read their own, service can do all
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON user_subscriptions TO conthunt_app;
GRANT ALL ON user_subscriptions TO conthunt_service;

DROP POLICY IF EXISTS subscriptions_select_own ON user_subscriptions;
CREATE POLICY subscriptions_select_own ON user_subscriptions FOR SELECT TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS subscriptions_service_all ON user_subscriptions;
CREATE POLICY subscriptions_service_all ON user_subscriptions FOR ALL TO conthunt_service
USING (true) WITH CHECK (true);

-- pending_plan_changes: Users can read their own, service can do all
ALTER TABLE pending_plan_changes ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON pending_plan_changes TO conthunt_app;
GRANT ALL ON pending_plan_changes TO conthunt_service;

DROP POLICY IF EXISTS pending_changes_select_own ON pending_plan_changes;
CREATE POLICY pending_changes_select_own ON pending_plan_changes FOR SELECT TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS pending_changes_service_all ON pending_plan_changes;
CREATE POLICY pending_changes_service_all ON pending_plan_changes FOR ALL TO conthunt_service
USING (true) WITH CHECK (true);

-- webhook_events: Service only (webhooks don't have user context)
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;
GRANT ALL ON webhook_events TO conthunt_service;

DROP POLICY IF EXISTS webhook_events_service_all ON webhook_events;
CREATE POLICY webhook_events_service_all ON webhook_events FOR ALL TO conthunt_service
USING (true) WITH CHECK (true);
