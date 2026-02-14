-- Step 2: Drop redundant indexes duplicated by PK/UNIQUE indexes
-- Run manually in SQL Studio.

SET search_path = conthunt, public;

-- Duplicate of idx_board_items_added (same definition)
DROP INDEX IF EXISTS conthunt.idx_board_items_by_board_added;

-- Duplicate of board_items primary key index (board_id, content_item_id)
DROP INDEX IF EXISTS conthunt.idx_board_items_composite;

-- Duplicate of unique constraint index on (user_id, flow_id)
DROP INDEX IF EXISTS conthunt.idx_onboarding_user_flow;

-- Duplicate of unique constraint index on twelvelabs_assets(media_asset_id)
DROP INDEX IF EXISTS conthunt.idx_twelvelabs_assets_media;

-- Duplicate of unique constraint index on user_analysis_access(user_id, media_asset_id)
DROP INDEX IF EXISTS conthunt.idx_user_analysis_access_lookup;

-- Duplicate of unique constraint index on user_streak_days(user_id, streak_type_id, activity_date)
DROP INDEX IF EXISTS conthunt.idx_user_streak_days_lookup;

-- Duplicate of unique constraint index on user_streaks(user_id, streak_type_id)
DROP INDEX IF EXISTS conthunt.idx_user_streaks_user_type;

-- Duplicate of unique constraint index on video_analyses(media_asset_id)
DROP INDEX IF EXISTS conthunt.idx_video_analyses_media;

-- Duplicate of unique constraint index on user_subscriptions(subscription_id)
DROP INDEX IF EXISTS conthunt.idx_user_subscriptions_subscription_id;
