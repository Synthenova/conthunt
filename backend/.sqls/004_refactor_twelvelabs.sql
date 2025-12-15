-- Refactor TwelveLabs integration to remove dynamic index management
-- and use a single static index ID from environment variables.

SET search_path = conthunt, public;

-- 1. Drop the FK constraint and column from twelvelabs_assets
ALTER TABLE conthunt.twelvelabs_assets 
DROP COLUMN twelvelabs_index_id CASCADE;

-- 2. Add the new text column for index_id
ALTER TABLE conthunt.twelvelabs_assets 
ADD COLUMN index_id text;

-- 3. Drop the now unused twelvelabs_indexes table
DROP TABLE conthunt.twelvelabs_indexes;
