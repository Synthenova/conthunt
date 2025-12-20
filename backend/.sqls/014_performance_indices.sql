-- Performance optimization indices
-- Run with CONCURRENTLY in production to avoid table locks

SET search_path = conthunt, public;

-- ============================================================================
-- CRITICAL: Missing foreign key indices
-- ============================================================================

-- 1. media_assets.content_item_id - Most critical missing index
-- Every query joining content_items → media_assets does full table scans without this
CREATE INDEX IF NOT EXISTS idx_media_assets_content_item
ON conthunt.media_assets(content_item_id);

-- 2. search_results.content_item_id - For search result lookups
CREATE INDEX IF NOT EXISTS idx_search_results_content_item
ON conthunt.search_results(content_item_id);

-- 3. Composite index for board_items (board_id already indexed, add content_item_id)
-- Note: idx_board_items_content already exists on content_item_id alone
-- This composite helps JOIN queries that filter by board_id
CREATE INDEX IF NOT EXISTS idx_board_items_composite
ON conthunt.board_items(board_id, content_item_id);

-- ============================================================================
-- Trigram indices for ILIKE text search
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- For board name search
CREATE INDEX IF NOT EXISTS idx_boards_name_trgm
ON conthunt.boards USING GIN (name gin_trgm_ops);

-- For content item title search
CREATE INDEX IF NOT EXISTS idx_content_items_title_trgm
ON conthunt.content_items USING GIN (title gin_trgm_ops);

-- For content item primary_text search (if frequently searched)
CREATE INDEX IF NOT EXISTS idx_content_items_text_trgm
ON conthunt.content_items USING GIN (primary_text gin_trgm_ops);

-- ============================================================================
-- Partial indices for filtered queries
-- ============================================================================

-- TwelveLabs assets with indexed_asset_id (only non-null values)
CREATE INDEX IF NOT EXISTS idx_twelvelabs_assets_indexed_partial
ON conthunt.twelvelabs_assets(indexed_asset_id)
WHERE indexed_asset_id IS NOT NULL;

-- Video analyses by status (for processing checks)
CREATE INDEX IF NOT EXISTS idx_video_analyses_status
ON conthunt.video_analyses(media_asset_id, status);

-- ============================================================================
-- Covering index for common query patterns
-- ============================================================================

-- For get_board_items: board_id -> added_at ordering
CREATE INDEX IF NOT EXISTS idx_board_items_added
ON conthunt.board_items(board_id, added_at DESC);
