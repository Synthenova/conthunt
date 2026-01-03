-- Create chat_tags table to store tagged boards, searches, and media per chat.
-- This intentionally keeps the existing context_type/context_id fields unchanged.

CREATE TABLE IF NOT EXISTS conthunt.chat_tags (
    id uuid PRIMARY KEY,
    chat_id uuid NOT NULL REFERENCES conthunt.chats(id) ON DELETE CASCADE,
    tag_type text NOT NULL CHECK (tag_type IN ('board', 'search', 'media')),
    tag_id uuid NOT NULL,
    tag_label text NULL,
    source text NOT NULL DEFAULT 'user' CHECK (source IN ('user', 'agent')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (chat_id, tag_type, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_chat_tags_chat_type ON conthunt.chat_tags (chat_id, tag_type);
