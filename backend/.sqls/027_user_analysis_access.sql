SET search_path = conthunt, public;

-- User Analysis Access Table
-- Tracks which users have accessed (and been charged for) each video analysis
-- This enables per-user credit deduction even when analysis results are cached globally

CREATE TABLE IF NOT EXISTS user_analysis_access (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    media_asset_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(user_id, media_asset_id)
);

-- Index for fast lookup by user + media_asset
CREATE INDEX IF NOT EXISTS idx_user_analysis_access_lookup 
    ON user_analysis_access (user_id, media_asset_id);

-- RLS Policies
ALTER TABLE user_analysis_access ENABLE ROW LEVEL SECURITY;

-- Grant permissions
GRANT SELECT, INSERT ON user_analysis_access TO conthunt_app;
GRANT ALL ON user_analysis_access TO conthunt_service;

-- Policy: Users can only see and insert their own access records (conthunt_app)
DROP POLICY IF EXISTS user_analysis_access_insert_own ON user_analysis_access;
CREATE POLICY user_analysis_access_insert_own ON user_analysis_access FOR INSERT TO conthunt_app
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS user_analysis_access_select_own ON user_analysis_access;
CREATE POLICY user_analysis_access_select_own ON user_analysis_access FOR SELECT TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);

-- Policy: Service role uses same RLS check (conthunt_service)
DROP POLICY IF EXISTS user_analysis_access_service_insert ON user_analysis_access;
CREATE POLICY user_analysis_access_service_insert ON user_analysis_access FOR INSERT TO conthunt_service
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS user_analysis_access_service_select ON user_analysis_access;
CREATE POLICY user_analysis_access_service_select ON user_analysis_access FOR SELECT TO conthunt_service
USING (user_id = current_setting('app.user_id', true)::uuid);
