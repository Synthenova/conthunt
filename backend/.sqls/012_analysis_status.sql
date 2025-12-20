-- Migration: Add status column to video_analyses for non-blocking polling
-- This enables the frontend to poll for analysis completion

ALTER TABLE video_analyses 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'processing';

-- Update existing records to 'completed' since they have results
UPDATE video_analyses SET status = 'completed' WHERE analysis_result IS NOT NULL;

-- Add error column for failed analyses
ALTER TABLE video_analyses 
ADD COLUMN IF NOT EXISTS error TEXT;

-- Create index for efficient polling queries
CREATE INDEX IF NOT EXISTS idx_video_analyses_status 
ON video_analyses(content_item_id, status);
