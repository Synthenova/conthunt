-- Run this AFTER 023_author_columns.sql completes

SET search_path = conthunt, public;

-- Index for potential author lookups (partial index - only non-null values)
-- Using regular CREATE INDEX (will briefly lock table during creation)
CREATE INDEX IF NOT EXISTS idx_content_items_author_id 
ON content_items(author_id) WHERE author_id IS NOT NULL;
