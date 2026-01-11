-- Credit System Migration
-- Resets all usage and creates credit-based tracking tables
SET search_path = conthunt, public;

-- ============================================================================
-- 1. RESET: Clear all existing usage data
-- ============================================================================
TRUNCATE TABLE usage_logs;
DROP TABLE IF EXISTS plan_limits CASCADE;

-- ============================================================================
-- 2. USERS: Simplify and add billing cycle tracking
-- ============================================================================
-- Remove redundant columns (can fetch from Dodo API)
ALTER TABLE users
  DROP COLUMN IF EXISTS dodo_product_id,
  DROP COLUMN IF EXISTS dodo_status,
  DROP COLUMN IF EXISTS dodo_updated_at;

-- Add billing cycle start (for credit period calculation)
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS current_period_start TIMESTAMPTZ;

-- ============================================================================
-- 3. NEW TABLES: Credit configuration
-- ============================================================================

-- Plan credit pools
CREATE TABLE IF NOT EXISTS plan_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_role TEXT NOT NULL UNIQUE,
    total_credits INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Feature credit costs
CREATE TABLE IF NOT EXISTS feature_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature TEXT NOT NULL UNIQUE,
    credit_cost INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Per-feature caps by plan
CREATE TABLE IF NOT EXISTS feature_caps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_role TEXT NOT NULL,
    feature TEXT NOT NULL,
    max_uses INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(plan_role, feature)
);

-- ============================================================================
-- 4. SEED DATA
-- ============================================================================

-- Credit pools per plan
INSERT INTO plan_credits (plan_role, total_credits) VALUES
('free', 50),
('creator', 1000),
('pro_research', 3000)
ON CONFLICT (plan_role) DO UPDATE SET total_credits = EXCLUDED.total_credits;

-- Feature credit costs
INSERT INTO feature_config (feature, credit_cost) VALUES
('search_query', 1),
('video_analysis', 2),
('index_video', 5)
ON CONFLICT (feature) DO UPDATE SET credit_cost = EXCLUDED.credit_cost;

-- Per-feature caps (search limits)
INSERT INTO feature_caps (plan_role, feature, max_uses) VALUES
('free', 'search_query', 5),
('creator', 'search_query', 50),
('pro_research', 'search_query', 150)
ON CONFLICT (plan_role, feature) DO UPDATE SET max_uses = EXCLUDED.max_uses;

-- ============================================================================
-- 5. RLS & PERMISSIONS
-- ============================================================================

ALTER TABLE plan_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_caps ENABLE ROW LEVEL SECURITY;

-- Read-only for app, full access for service
GRANT SELECT ON plan_credits TO conthunt_app;
GRANT SELECT ON feature_config TO conthunt_app;
GRANT SELECT ON feature_caps TO conthunt_app;

GRANT ALL ON plan_credits TO conthunt_service;
GRANT ALL ON feature_config TO conthunt_service;
GRANT ALL ON feature_caps TO conthunt_service;

-- Everyone can read config tables
DROP POLICY IF EXISTS credits_select_all ON plan_credits;
CREATE POLICY credits_select_all ON plan_credits FOR SELECT USING (true);

DROP POLICY IF EXISTS config_select_all ON feature_config;
CREATE POLICY config_select_all ON feature_config FOR SELECT USING (true);

DROP POLICY IF EXISTS caps_select_all ON feature_caps;
CREATE POLICY caps_select_all ON feature_caps FOR SELECT USING (true);
