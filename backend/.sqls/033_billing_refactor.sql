-- Billing System Refactor
-- Creates robust tables for idempotent webhook handling, product caching,
-- normalized subscription state, and scheduled plan changes.
SET search_path = conthunt, public;

-- ============================================================================
-- 1. DODO_PRODUCTS: Cached product catalog from Dodo API
-- ============================================================================
-- Stores product info with metadata for dynamic role mapping.
-- Populated lazily when webhooks arrive, or via periodic sync.

CREATE TABLE IF NOT EXISTS dodo_products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_recurring BOOLEAN NOT NULL DEFAULT true,
    price INTEGER, -- Price in lowest denomination (cents)
    currency TEXT DEFAULT 'USD',
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB, -- Contains app_role, monthly_credits, etc.
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw JSONB -- Full API response for debugging
);

CREATE INDEX IF NOT EXISTS idx_dodo_products_recurring ON dodo_products(is_recurring) WHERE is_recurring = true;

-- ============================================================================
-- 2. USER_SUBSCRIPTIONS: Normalized subscription state (source of truth)
-- ============================================================================
-- One row per user's active/recent subscription. Updated on every webhook.
-- Contains the full snapshot from Dodo for accurate state.

CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id TEXT NOT NULL UNIQUE,
    customer_id TEXT,
    product_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- active, on_hold, cancelled, expired, pending, trialing
    cancel_at_next_billing_date BOOLEAN NOT NULL DEFAULT false,
    cancelled_at TIMESTAMPTZ,
    current_period_start TIMESTAMPTZ, -- From Dodo's previous_billing_date
    current_period_end TIMESTAMPTZ, -- From Dodo's next_billing_date
    expires_at TIMESTAMPTZ,
    last_event_ts TIMESTAMPTZ NOT NULL, -- For out-of-order protection
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_customer_id ON user_subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);

-- ============================================================================
-- 3. PENDING_PLAN_CHANGES: Scheduled downgrades
-- ============================================================================
-- Stores user intent to downgrade at end of billing cycle.
-- Applied by webhook handler when renewal event arrives.

CREATE TABLE IF NOT EXISTS pending_plan_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id TEXT NOT NULL,
    current_product_id TEXT NOT NULL,
    target_product_id TEXT NOT NULL,
    target_role TEXT NOT NULL, -- The app role they're downgrading to
    effective_at TIMESTAMPTZ NOT NULL, -- When to apply (= current_period_end)
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'applied', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    applied_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pending_plan_changes_user_id ON pending_plan_changes(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_plan_changes_status ON pending_plan_changes(status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_pending_plan_changes_effective ON pending_plan_changes(effective_at) WHERE status = 'pending';

-- ============================================================================
-- 4. WEBHOOK_EVENTS: Enhanced audit trail (replaces dodo_webhook_events)
-- ============================================================================
-- Full webhook storage for idempotency, debugging, and replay.

-- Drop old minimal table if exists
DROP TABLE IF EXISTS dodo_webhook_events;

CREATE TABLE IF NOT EXISTS webhook_events (
    webhook_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    event_ts TIMESTAMPTZ NOT NULL, -- Timestamp from event payload
    subscription_id TEXT, -- For querying related events
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    process_status TEXT DEFAULT 'pending' CHECK (process_status IN ('pending', 'ok', 'error', 'skipped')),
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_subscription ON webhook_events(subscription_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_type ON webhook_events(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_events_received ON webhook_events(received_at DESC);

-- ============================================================================
-- 5. RLS & PERMISSIONS
-- ============================================================================

-- dodo_products: Read-only for app, full for service
ALTER TABLE dodo_products ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON dodo_products TO conthunt_app;
GRANT ALL ON dodo_products TO conthunt_service;

DROP POLICY IF EXISTS products_select_all ON dodo_products;
CREATE POLICY products_select_all ON dodo_products FOR SELECT USING (true);

-- user_subscriptions: Users can only see their own
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON user_subscriptions TO conthunt_app;
GRANT ALL ON user_subscriptions TO conthunt_service;

DROP POLICY IF EXISTS subscriptions_select_own ON user_subscriptions;
CREATE POLICY subscriptions_select_own ON user_subscriptions FOR SELECT TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS subscriptions_insert_own ON user_subscriptions;
CREATE POLICY subscriptions_insert_own ON user_subscriptions FOR INSERT TO conthunt_app
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS subscriptions_update_own ON user_subscriptions;
CREATE POLICY subscriptions_update_own ON user_subscriptions FOR UPDATE TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);

-- Service role bypass for webhooks (no RLS check)
DROP POLICY IF EXISTS subscriptions_service_all ON user_subscriptions;
CREATE POLICY subscriptions_service_all ON user_subscriptions FOR ALL TO conthunt_service
USING (true) WITH CHECK (true);

-- pending_plan_changes: Users can see/modify their own
ALTER TABLE pending_plan_changes ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON pending_plan_changes TO conthunt_app;
GRANT ALL ON pending_plan_changes TO conthunt_service;

DROP POLICY IF EXISTS pending_changes_select_own ON pending_plan_changes;
CREATE POLICY pending_changes_select_own ON pending_plan_changes FOR SELECT TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS pending_changes_insert_own ON pending_plan_changes;
CREATE POLICY pending_changes_insert_own ON pending_plan_changes FOR INSERT TO conthunt_app
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS pending_changes_update_own ON pending_plan_changes;
CREATE POLICY pending_changes_update_own ON pending_plan_changes FOR UPDATE TO conthunt_app
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