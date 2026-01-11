-- backend/.sqls/015_chat_context.sql
SET search_path = conthunt, public;

ALTER TABLE conthunt.chats
  ADD COLUMN context_type text,
  ADD COLUMN context_id uuid,
  ADD CONSTRAINT chats_context_type_check
    CHECK (context_type IN ('board', 'search'));

CREATE INDEX idx_chats_context_updated
  ON conthunt.chats(context_type, context_id, updated_at DESC);
