-- Remove FTS generated columns (fastest writes; removes stored tsvector maintenance).
-- Transaction-safe (no CONCURRENTLY).

SET search_path = conthunt, public;

ALTER TABLE conthunt.content_items
DROP COLUMN IF EXISTS fts;

ALTER TABLE conthunt.boards
DROP COLUMN IF EXISTS fts;

