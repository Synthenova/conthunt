-- Onboarding Tutorial Progress Tracking
-- Tracks user progress through linear tutorial flows per page
SET search_path = conthunt, public;

-- ============================================================================
-- 1. User Onboarding Progress (one row per user + flow)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_onboarding_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    flow_id VARCHAR(50) NOT NULL,
    
    -- Progress tracking
    current_step INT NOT NULL DEFAULT 0,  -- 0 = not started, 1+ = step index
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',  -- not_started, in_progress, completed, skipped
    
    -- Timestamps
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Replay tracking
    restart_count INT NOT NULL DEFAULT 0,
    
    UNIQUE(user_id, flow_id)
);

CREATE INDEX IF NOT EXISTS idx_onboarding_user_flow
    ON user_onboarding_progress(user_id, flow_id);

-- ============================================================================
-- 2. Grants
-- ============================================================================
GRANT SELECT, INSERT, UPDATE ON user_onboarding_progress TO conthunt_app;
GRANT ALL ON user_onboarding_progress TO conthunt_service;

-- ============================================================================
-- 3. RLS Policies
-- ============================================================================
ALTER TABLE user_onboarding_progress ENABLE ROW LEVEL SECURITY;

-- App role policies
DROP POLICY IF EXISTS onboarding_select_own ON user_onboarding_progress;
CREATE POLICY onboarding_select_own ON user_onboarding_progress FOR SELECT
TO conthunt_app, conthunt_service
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS onboarding_insert_own ON user_onboarding_progress;
CREATE POLICY onboarding_insert_own ON user_onboarding_progress FOR INSERT
TO conthunt_app, conthunt_service
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS onboarding_update_own ON user_onboarding_progress;
CREATE POLICY onboarding_update_own ON user_onboarding_progress FOR UPDATE
TO conthunt_app, conthunt_service
USING (user_id = current_setting('app.user_id', true)::uuid)
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
