-- Add Postgres FTS support (tsvector generated columns + GIN indexes).
--
-- This migration is written to be transaction-safe (no CONCURRENTLY). If you need
-- non-blocking index builds in production, run CREATE/DROP INDEX CONCURRENTLY manually.

SET search_path = conthunt, public;

-- Boards: searchable name
ALTER TABLE conthunt.boards
ADD COLUMN IF NOT EXISTS fts tsvector
GENERATED ALWAYS AS (
    to_tsvector('english', coalesce(name, ''))
) STORED;

CREATE INDEX IF NOT EXISTS idx_boards_fts
ON conthunt.boards USING GIN (fts);

-- Content items: searchable title + primary_text (weighted title > text)
ALTER TABLE conthunt.content_items
ADD COLUMN IF NOT EXISTS fts tsvector
GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(primary_text, '')), 'B')
) STORED;

CREATE INDEX IF NOT EXISTS idx_content_items_fts
ON conthunt.content_items USING GIN (fts);

-- Remove old trigram indexes (FTS-only search; no substrings).
DROP INDEX IF EXISTS conthunt.idx_content_items_title_trgm;
DROP INDEX IF EXISTS conthunt.idx_content_items_text_trgm;
DROP INDEX IF EXISTS conthunt.idx_boards_name_trgm;
