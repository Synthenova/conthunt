-- Rewards refactor: separate credits bonus from feature bonus, and clear existing reward data
SET search_path = conthunt, public;

-- Remove existing reward data (dev only)
TRUNCATE TABLE streak_reward_grants;
TRUNCATE TABLE reward_balances;
DELETE FROM streak_milestones;

-- Update milestones schema for new reward model
ALTER TABLE streak_milestones
    DROP COLUMN IF EXISTS reward_amount;

ALTER TABLE streak_milestones
    ADD COLUMN IF NOT EXISTS reward_credits INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS reward_feature_amount INT NOT NULL DEFAULT 0;

ALTER TABLE streak_milestones
    ALTER COLUMN reward_feature DROP NOT NULL;

-- Update reward grants schema to match milestones
ALTER TABLE streak_reward_grants
    DROP COLUMN IF EXISTS reward_amount;

ALTER TABLE streak_reward_grants
    ADD COLUMN IF NOT EXISTS reward_credits INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS reward_feature_amount INT NOT NULL DEFAULT 0;

-- Allow NULL reward_feature for global credits and enforce uniqueness
ALTER TABLE reward_balances
    DROP CONSTRAINT IF EXISTS reward_balances_pkey;

ALTER TABLE reward_balances
    ADD COLUMN IF NOT EXISTS id UUID PRIMARY KEY DEFAULT gen_random_uuid();

ALTER TABLE reward_balances
    ALTER COLUMN reward_feature DROP NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS reward_balances_unique_feature
    ON reward_balances (user_id, reward_feature)
    WHERE reward_feature IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS reward_balances_unique_credits
    ON reward_balances (user_id)
    WHERE reward_feature IS NULL;
