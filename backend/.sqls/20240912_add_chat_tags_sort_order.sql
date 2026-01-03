-- Add sort_order to chat_tags to support ordered search tabs.

ALTER TABLE conthunt.chat_tags
ADD COLUMN IF NOT EXISTS sort_order int;

-- Backfill existing rows to preserve "newest first" ordering.
-- Use created_at descending mapped to negative sequence so smaller numbers are "top".
WITH ordered AS (
    SELECT id, row_number() OVER (ORDER BY created_at DESC) AS rn
    FROM conthunt.chat_tags
    WHERE sort_order IS NULL
)
UPDATE conthunt.chat_tags AS ct
SET sort_order = -ordered.rn
FROM ordered
WHERE ct.id = ordered.id;

CREATE INDEX IF NOT EXISTS idx_chat_tags_chat_order ON conthunt.chat_tags (chat_id, sort_order);
