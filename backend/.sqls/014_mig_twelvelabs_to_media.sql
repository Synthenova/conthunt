-- Migration: Refactor twelvelabs_assets and video_analyses to link to media_assets
-- instead of content_items.
--
-- This migration:
-- 1. Adds media_asset_id columns (nullable initially)
-- 2. Backfills data from existing content_item_id -> media_assets (video type)
-- 3. Makes media_asset_id NOT NULL and adds FK constraints
-- 4. Drops the old content_item_id columns and related constraints

SET search_path = conthunt, public;

-- ============================================================================
-- Step 1: Add new media_asset_id columns (nullable for now)
-- ============================================================================

ALTER TABLE conthunt.twelvelabs_assets
ADD COLUMN media_asset_id uuid;

ALTER TABLE conthunt.video_analyses
ADD COLUMN media_asset_id uuid;


-- ============================================================================
-- Step 2: Backfill media_asset_id from content_item_id
-- For each row, find the video-type media_asset for that content_item
-- ============================================================================

-- Backfill twelvelabs_assets
UPDATE conthunt.twelvelabs_assets ta
SET media_asset_id = (
    SELECT ma.id
    FROM conthunt.media_assets ma
    WHERE ma.content_item_id = ta.content_item_id
      AND ma.asset_type = 'video'
    ORDER BY ma.created_at DESC
    LIMIT 1
)
WHERE ta.media_asset_id IS NULL;

-- Backfill video_analyses
UPDATE conthunt.video_analyses va
SET media_asset_id = (
    SELECT ma.id
    FROM conthunt.media_assets ma
    WHERE ma.content_item_id = va.content_item_id
      AND ma.asset_type = 'video'
    ORDER BY ma.created_at DESC
    LIMIT 1
)
WHERE va.media_asset_id IS NULL;


-- ============================================================================
-- Step 3: Handle orphaned rows (content_items with no video asset)
-- Option A: Delete them (uncomment if desired)
-- Option B: Leave them with NULL media_asset_id (current approach - will fail NOT NULL)
-- 
-- For safety, we'll delete orphaned rows that couldn't be migrated:
-- ============================================================================

DELETE FROM conthunt.twelvelabs_assets WHERE media_asset_id IS NULL;
DELETE FROM conthunt.video_analyses WHERE media_asset_id IS NULL;


-- ============================================================================
-- Step 4: Add NOT NULL constraint and FK references
-- ============================================================================

ALTER TABLE conthunt.twelvelabs_assets
ALTER COLUMN media_asset_id SET NOT NULL;

ALTER TABLE conthunt.twelvelabs_assets
ADD CONSTRAINT fk_twelvelabs_assets_media_asset
FOREIGN KEY (media_asset_id) REFERENCES conthunt.media_assets(id) ON DELETE CASCADE;

ALTER TABLE conthunt.video_analyses
ALTER COLUMN media_asset_id SET NOT NULL;

ALTER TABLE conthunt.video_analyses
ADD CONSTRAINT fk_video_analyses_media_asset
FOREIGN KEY (media_asset_id) REFERENCES conthunt.media_assets(id) ON DELETE CASCADE;


-- ============================================================================
-- Step 5: Drop old content_item_id columns
-- This also drops the UNIQUE constraint on content_item_id
-- ============================================================================

-- First drop the FK constraint on video_analyses.twelvelabs_asset_id referencing twelvelabs_assets
-- (We'll keep this reference, it's fine)

-- Drop the unique constraint on content_item_id before dropping the column
ALTER TABLE conthunt.twelvelabs_assets DROP CONSTRAINT IF EXISTS twelvelabs_assets_content_item_id_key;
ALTER TABLE conthunt.video_analyses DROP CONSTRAINT IF EXISTS video_analyses_content_item_id_key;

-- Drop the columns
ALTER TABLE conthunt.twelvelabs_assets DROP COLUMN content_item_id;
ALTER TABLE conthunt.video_analyses DROP COLUMN content_item_id;


-- ============================================================================
-- Step 6: Create new unique constraint on media_asset_id
-- (One TwelveLabs asset per media file, one analysis per media file)
-- ============================================================================

ALTER TABLE conthunt.twelvelabs_assets
ADD CONSTRAINT twelvelabs_assets_media_asset_id_key UNIQUE (media_asset_id);

ALTER TABLE conthunt.video_analyses
ADD CONSTRAINT video_analyses_media_asset_id_key UNIQUE (media_asset_id);


-- ============================================================================
-- Step 7: Update indices
-- ============================================================================

DROP INDEX IF EXISTS conthunt.idx_twelvelabs_assets_content;
DROP INDEX IF EXISTS conthunt.idx_video_analyses_content;

CREATE INDEX idx_twelvelabs_assets_media ON conthunt.twelvelabs_assets(media_asset_id);
CREATE INDEX idx_video_analyses_media ON conthunt.video_analyses(media_asset_id);


-- ============================================================================
-- Done!
-- ============================================================================
