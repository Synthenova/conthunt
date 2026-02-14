-- Disable FTS indexing (keep generated columns so it can be re-enabled later).
-- Transaction-safe (no CONCURRENTLY).

SET search_path = conthunt, public;

DROP INDEX IF EXISTS conthunt.idx_content_items_fts;
DROP INDEX IF EXISTS conthunt.idx_boards_fts;

