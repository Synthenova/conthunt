-- Streak Reward Claims (manual claim + persistent balances)
SET search_path = conthunt, public;

-- ============================================================================
-- 1. Reward metadata on milestones
-- ============================================================================
ALTER TABLE streak_milestones
    ADD COLUMN IF NOT EXISTS reward_feature TEXT,
    ADD COLUMN IF NOT EXISTS reward_amount INT;

-- ============================================================================
-- 2. Reward grants (one-time claims)
-- ============================================================================
CREATE TABLE IF NOT EXISTS streak_reward_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    streak_type_id UUID NOT NULL REFERENCES streak_types(id) ON DELETE CASCADE,
    days_required INT NOT NULL,
    role TEXT NOT NULL,
    reward_feature TEXT NOT NULL,
    reward_amount INT NOT NULL,
    claimed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, streak_type_id, days_required, role)
);

CREATE INDEX IF NOT EXISTS idx_streak_reward_grants_user_type
    ON streak_reward_grants (user_id, streak_type_id);

-- ============================================================================
-- 3. Reward balances (persist across periods)
-- ============================================================================
CREATE TABLE IF NOT EXISTS reward_balances (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reward_feature TEXT NOT NULL,
    balance INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, reward_feature)
);

-- ============================================================================
-- 4. RLS & Permissions
-- ============================================================================
ALTER TABLE streak_reward_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE reward_balances ENABLE ROW LEVEL SECURITY;

-- Grants for app role
GRANT SELECT, INSERT ON streak_reward_grants TO conthunt_app;
GRANT SELECT, INSERT, UPDATE ON reward_balances TO conthunt_app;

-- Grants for service role
GRANT ALL ON streak_reward_grants TO conthunt_service;
GRANT ALL ON reward_balances TO conthunt_service;

-- Policies: user-scoped tables (app + service)
DROP POLICY IF EXISTS streak_reward_grants_select_own ON streak_reward_grants;
CREATE POLICY streak_reward_grants_select_own ON streak_reward_grants FOR SELECT
TO conthunt_app, conthunt_service
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS streak_reward_grants_insert_own ON streak_reward_grants;
CREATE POLICY streak_reward_grants_insert_own ON streak_reward_grants FOR INSERT
TO conthunt_app, conthunt_service
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS reward_balances_select_own ON reward_balances;
CREATE POLICY reward_balances_select_own ON reward_balances FOR SELECT
TO conthunt_app, conthunt_service
USING (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS reward_balances_insert_own ON reward_balances;
CREATE POLICY reward_balances_insert_own ON reward_balances FOR INSERT
TO conthunt_app, conthunt_service
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS reward_balances_update_own ON reward_balances;
CREATE POLICY reward_balances_update_own ON reward_balances FOR UPDATE
TO conthunt_app, conthunt_service
USING (user_id = current_setting('app.user_id', true)::uuid)
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
