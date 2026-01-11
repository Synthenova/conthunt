-- Add author columns to content_items table for direct storage
-- This eliminates the need to extract author info from JSONB payload at query time

SET search_path = conthunt, public;

-- Add author columns
ALTER TABLE content_items
ADD COLUMN IF NOT EXISTS author_id TEXT,
ADD COLUMN IF NOT EXISTS author_name TEXT,
ADD COLUMN IF NOT EXISTS author_url TEXT,
ADD COLUMN IF NOT EXISTS author_image_url TEXT;

-- Backfill existing data from payload
-- This uses the exact same extraction logic as content_builder.py
UPDATE content_items SET
  author_id = CASE 
    WHEN platform LIKE 'tiktok%' THEN payload->'author'->>'uid'
    WHEN platform = 'instagram' THEN payload->'owner'->>'id'
    WHEN platform = 'youtube' THEN payload->'channel'->>'id'
    WHEN platform = 'pinterest' THEN payload->'pinner'->>'id'
  END,
  author_name = CASE 
    WHEN platform LIKE 'tiktok%' THEN payload->'author'->>'nickname'
    WHEN platform = 'instagram' THEN payload->'owner'->>'full_name'
    WHEN platform = 'youtube' THEN COALESCE(payload->'channel'->>'name', payload->'channel'->>'title')
    WHEN platform = 'pinterest' THEN payload->'pinner'->>'full_name'
  END,
  author_url = CASE 
    WHEN platform LIKE 'tiktok%' THEN 'https://www.tiktok.com/@' || creator_handle
    WHEN platform = 'instagram' THEN 'https://www.instagram.com/' || (payload->'owner'->>'username') || '/'
    WHEN platform = 'youtube' THEN COALESCE(payload->'channel'->>'url', 'https://www.youtube.com/' || (payload->'channel'->>'handle'))
    WHEN platform = 'pinterest' THEN 'https://www.pinterest.com/' || (payload->'pinner'->>'username') || '/'
  END,
  author_image_url = CASE 
    WHEN platform LIKE 'tiktok%' THEN payload->'author'->>'avatar'
    WHEN platform = 'instagram' THEN payload->'owner'->>'profile_pic_url'
    WHEN platform = 'youtube' THEN payload->'channel'->>'thumbnail'
    WHEN platform = 'pinterest' THEN payload->'pinner'->>'image_medium_url'
  END
WHERE author_id IS NULL AND payload IS NOT NULL;
