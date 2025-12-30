SET search_path = conthunt, public;

-- 1. Usage Logs Table
-- Tracks every usage event with timestamp and context
CREATE TABLE IF NOT EXISTS usage_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature text NOT NULL, -- e.g. 'gemini_analysis', 'search_query'
    quantity int NOT NULL DEFAULT 1,
    context jsonb NOT NULL DEFAULT '{}'::jsonb, -- Store media_asset_id, associated cost, etc.
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Index for efficient querying of usage by feature and time period
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_feature_date ON usage_logs (user_id, feature, created_at DESC);

-- 2. Plan Limits Table
-- Defines rate limits and quotas for each plan role and feature
CREATE TABLE IF NOT EXISTS plan_limits (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_role text NOT NULL, -- Matches conthunt.users.role ('free', 'creator', 'pro_research')
    feature text NOT NULL,
    period text NOT NULL CHECK (period IN ('hourly', 'daily', 'monthly', 'yearly', 'total')),
    limit_count int NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(plan_role, feature, period)
);

-- 3. Initial Seed Data
-- Default limits for existing roles (adjust as needed)
INSERT INTO plan_limits (plan_role, feature, period, limit_count) VALUES
('free', 'gemini_analysis', 'daily', 5),
('creator', 'gemini_analysis', 'daily', 50),
('pro_research', 'gemini_analysis', 'daily', 500)
ON CONFLICT (plan_role, feature, period) 
DO UPDATE SET limit_count = EXCLUDED.limit_count;

-- 4. RLS Policies
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_limits ENABLE ROW LEVEL SECURITY;

-- Grant permissions to verified app users
GRANT SELECT, INSERT ON usage_logs TO conthunt_app;
GRANT SELECT ON plan_limits TO conthunt_app;

-- Grant full permissions to service role (admin/background tasks)
GRANT ALL ON usage_logs TO conthunt_service;
GRANT ALL ON plan_limits TO conthunt_service;

-- Policy: Users can only see and insert their own usage logs
DROP POLICY IF EXISTS usage_insert_own ON usage_logs;
CREATE POLICY usage_insert_own ON usage_logs FOR INSERT TO conthunt_app
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS usage_select_own ON usage_logs;
CREATE POLICY usage_select_own ON usage_logs FOR SELECT TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);

-- Policy: All authenticated users can read the plan limits (public configuration)
DROP POLICY IF EXISTS limits_select_all ON plan_limits;
CREATE POLICY limits_select_all ON plan_limits FOR SELECT TO conthunt_app
USING (true);
