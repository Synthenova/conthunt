-- Add soft-delete support for chat_tags

ALTER TABLE conthunt.chat_tags
ADD COLUMN IF NOT EXISTS deleted_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_chat_tags_not_deleted 
ON conthunt.chat_tags (chat_id) WHERE deleted_at IS NULL;
