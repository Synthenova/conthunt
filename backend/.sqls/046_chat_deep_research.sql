SET search_path = conthunt, public;

ALTER TABLE conthunt.chats
ADD COLUMN IF NOT EXISTS deep_research_enabled boolean NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_chats_deep_research_enabled
ON conthunt.chats (deep_research_enabled);
