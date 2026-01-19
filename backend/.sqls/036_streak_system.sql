-- Streak System Migration
-- Tracks daily app usage streaks (app open + 1 search per day)
SET search_path = conthunt, public;

-- ============================================================================
-- 1. User Streaks Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_streaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    last_activity_date DATE,              -- Last date user completed daily requirement
    last_search_at TIMESTAMPTZ,           -- Last search timestamp
    last_app_open_at TIMESTAMPTZ,         -- Last app open timestamp
    timezone TEXT NOT NULL DEFAULT 'UTC', -- User's timezone for day boundary
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for quick user lookups
CREATE INDEX IF NOT EXISTS idx_user_streaks_user_id ON user_streaks(user_id);

-- ============================================================================
-- 2. Milestone Configuration
-- ============================================================================
CREATE TABLE IF NOT EXISTS streak_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    days_required INT NOT NULL UNIQUE,
    reward_description TEXT NOT NULL,
    icon_name TEXT NOT NULL DEFAULT 'gift',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed milestone data (matching reference design)
INSERT INTO streak_milestones (days_required, reward_description, icon_name) VALUES
(10, '500 Credits', 'gift'),
(50, '2,000 Credits + T-Shirt', 'shirt'),
(100, '5,000 Credits + Hoodie', 'package'),
(365, 'Exclusive NYC Event Invite', 'plane')
ON CONFLICT (days_required) DO UPDATE SET 
    reward_description = EXCLUDED.reward_description,
    icon_name = EXCLUDED.icon_name;

-- ============================================================================
-- 3. RLS & Permissions
-- ============================================================================
ALTER TABLE user_streaks ENABLE ROW LEVEL SECURITY;
ALTER TABLE streak_milestones ENABLE ROW LEVEL SECURITY;

-- Grant permissions to app role
GRANT SELECT, INSERT, UPDATE ON user_streaks TO conthunt_app;
GRANT SELECT ON streak_milestones TO conthunt_app;

-- Grant full permissions to service role
GRANT ALL ON user_streaks TO conthunt_service;
GRANT ALL ON streak_milestones TO conthunt_service;

-- Policy: Users can only access their own streak data
DROP POLICY IF EXISTS streak_select_own ON user_streaks;
CREATE POLICY streak_select_own ON user_streaks FOR SELECT TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS streak_insert_own ON user_streaks;
CREATE POLICY streak_insert_own ON user_streaks FOR INSERT TO conthunt_app
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS streak_update_own ON user_streaks;
CREATE POLICY streak_update_own ON user_streaks FOR UPDATE TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid)
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

-- Everyone can read milestones (public configuration)
DROP POLICY IF EXISTS milestones_select_all ON streak_milestones;
CREATE POLICY milestones_select_all ON streak_milestones FOR SELECT TO conthunt_app
USING (true);
