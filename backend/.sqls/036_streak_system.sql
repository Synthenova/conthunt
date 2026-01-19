-- Streak System Migration (multi-type + daily ledger)
-- Tracks daily activity streaks per type (open, search, analysis)
SET search_path = conthunt, public;

-- ============================================================================
-- 0. Users timezone (source of truth)
-- ============================================================================
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS timezone TEXT NOT NULL DEFAULT 'UTC';

-- ============================================================================
-- 1. Streak Types
-- ============================================================================
CREATE TABLE IF NOT EXISTS streak_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 2. User Streaks (one row per user + type)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_streaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    streak_type_id UUID NOT NULL REFERENCES streak_types(id) ON DELETE CASCADE,
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    last_activity_date DATE,
    last_action_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, streak_type_id)
);

CREATE INDEX IF NOT EXISTS idx_user_streaks_user_type
    ON user_streaks (user_id, streak_type_id);

-- ============================================================================
-- 3. Daily Ledger (idempotent per day + type)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_streak_days (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    streak_type_id UUID NOT NULL REFERENCES streak_types(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    first_activity_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, streak_type_id, activity_date)
);

CREATE INDEX IF NOT EXISTS idx_user_streak_days_lookup
    ON user_streak_days (user_id, streak_type_id, activity_date);

-- ============================================================================
-- 4. Milestones (per role + type)
-- ============================================================================
CREATE TABLE IF NOT EXISTS streak_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role TEXT NOT NULL,
    streak_type_id UUID NOT NULL REFERENCES streak_types(id) ON DELETE CASCADE,
    days_required INT NOT NULL,
    reward_description TEXT NOT NULL,
    icon_name TEXT NOT NULL DEFAULT 'gift',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (role, streak_type_id, days_required)
);

-- ============================================================================
-- 5. RLS & Permissions
-- ============================================================================
ALTER TABLE streak_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_streaks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_streak_days ENABLE ROW LEVEL SECURITY;
ALTER TABLE streak_milestones ENABLE ROW LEVEL SECURITY;

-- Grants for app role
GRANT SELECT ON streak_types TO conthunt_app;
GRANT SELECT ON streak_milestones TO conthunt_app;
GRANT SELECT, INSERT, UPDATE ON user_streaks TO conthunt_app;
GRANT SELECT, INSERT ON user_streak_days TO conthunt_app;

-- Grants for service role
GRANT ALL ON streak_types TO conthunt_service;
GRANT ALL ON streak_milestones TO conthunt_service;
GRANT ALL ON user_streaks TO conthunt_service;
GRANT ALL ON user_streak_days TO conthunt_service;

-- Policies: user-scoped tables (app + service)
DROP POLICY IF EXISTS user_streaks_select_own ON user_streaks;
CREATE POLICY user_streaks_select_own ON user_streaks FOR SELECT
TO conthunt_app, conthunt_service
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS user_streaks_insert_own ON user_streaks;
CREATE POLICY user_streaks_insert_own ON user_streaks FOR INSERT
TO conthunt_app, conthunt_service
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS user_streaks_update_own ON user_streaks;
CREATE POLICY user_streaks_update_own ON user_streaks FOR UPDATE
TO conthunt_app, conthunt_service
USING (user_id = current_setting('app.user_id', true)::uuid)
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS user_streak_days_select_own ON user_streak_days;
CREATE POLICY user_streak_days_select_own ON user_streak_days FOR SELECT
TO conthunt_app, conthunt_service
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS user_streak_days_insert_own ON user_streak_days;
CREATE POLICY user_streak_days_insert_own ON user_streak_days FOR INSERT
TO conthunt_app, conthunt_service
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

-- Policies: shared tables (app + service)
DROP POLICY IF EXISTS streak_types_select_all ON streak_types;
CREATE POLICY streak_types_select_all ON streak_types FOR SELECT
TO conthunt_app, conthunt_service
USING (true);

DROP POLICY IF EXISTS streak_milestones_select_all ON streak_milestones;
CREATE POLICY streak_milestones_select_all ON streak_milestones FOR SELECT
TO conthunt_app, conthunt_service
USING (true);
