-- Step 1: Add high-impact indexes for search/board/media query paths
-- Run manually in SQL Studio.

SET search_path = conthunt, public;

-- platform_calls lookups by search_id + created_at
CREATE INDEX IF NOT EXISTS idx_platform_calls_search_created
ON conthunt.platform_calls (search_id, created_at);

-- latest cursor per platform for a given search
CREATE INDEX IF NOT EXISTS idx_platform_calls_search_platform_cursor_created
ON conthunt.platform_calls (search_id, platform, created_at DESC)
WHERE next_cursor IS NOT NULL;

-- ordered search results reads and max-rank lookups
CREATE INDEX IF NOT EXISTS idx_search_results_search_rank
ON conthunt.search_results (search_id, rank);

-- media asset lookups by content item + asset type, with latest-first ordering
CREATE INDEX IF NOT EXISTS idx_media_assets_content_asset_created
ON conthunt.media_assets (content_item_id, asset_type, created_at DESC);

-- board listing by user with updated_at sort
CREATE INDEX IF NOT EXISTS idx_boards_user_updated
ON conthunt.boards (user_id, updated_at DESC);
