-- Add status column to searches table
-- Possible values: 'running', 'completed', 'failed'
SET search_path TO conthunt, public;

ALTER TABLE searches ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'running';

-- Index for filtering by status (useful for history page)
CREATE INDEX IF NOT EXISTS idx_searches_status ON searches (status);

-- Update existing searches to 'completed' (they finished before this migration)
UPDATE searches SET status = 'completed' WHERE status = 'running';
