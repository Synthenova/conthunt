-- Optimization: Add composite index for board_items to support efficient sorting by added_at
CREATE INDEX IF NOT EXISTS idx_board_items_by_board_added 
ON conthunt.board_items (board_id, added_at DESC);
