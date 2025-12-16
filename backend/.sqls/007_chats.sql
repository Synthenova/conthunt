-- backend/.sqls/007_chats.sql
SET search_path = conthunt, public;

-- 1) Chat metadata (NO message storage)
CREATE TABLE conthunt.chats (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        uuid NOT NULL REFERENCES conthunt.users(id) ON DELETE CASCADE,
  thread_id      text NOT NULL UNIQUE, -- thread_id from LangGraph (string/uuid-like)
  title          text,
  status         text NOT NULL DEFAULT 'idle'
                 CHECK (status IN ('idle','running','needs_input','failed')),
  active_run_id  text,                 -- langgraph run_id (optional but useful)
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  deleted_at     timestamptz
);

CREATE INDEX idx_chats_user_updated ON conthunt.chats(user_id, updated_at DESC);

-- 2) Cursor/state for reconnectable streaming
CREATE TABLE conthunt.chat_stream_state (
  chat_id                uuid PRIMARY KEY REFERENCES conthunt.chats(id) ON DELETE CASCADE,
  last_redis_stream_id    text,  -- e.g. "1700000000000-0"
  last_langgraph_event_id text,  -- StreamPart.id (for join_stream resume)
  updated_at              timestamptz NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON conthunt.chats TO conthunt_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON conthunt.chat_stream_state TO conthunt_app;

ALTER TABLE conthunt.chats FORCE ROW LEVEL SECURITY;
ALTER TABLE conthunt.chat_stream_state FORCE ROW LEVEL SECURITY;

-- RLS (same style as boards/searches)
CREATE POLICY chats_select_own
  ON conthunt.chats FOR SELECT TO conthunt_app
  USING (user_id = current_setting('app.user_id', true)::uuid);

CREATE POLICY chats_insert_own
  ON conthunt.chats FOR INSERT TO conthunt_app
  WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

CREATE POLICY chats_update_own
  ON conthunt.chats FOR UPDATE TO conthunt_app
  USING (user_id = current_setting('app.user_id', true)::uuid)
  WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

CREATE POLICY chats_delete_own
  ON conthunt.chats FOR DELETE TO conthunt_app
  USING (user_id = current_setting('app.user_id', true)::uuid);

CREATE POLICY chat_stream_state_rw_own
  ON conthunt.chat_stream_state FOR ALL TO conthunt_app
  USING (
    chat_id IN (SELECT id FROM conthunt.chats
                WHERE user_id = current_setting('app.user_id', true)::uuid)
  )
  WITH CHECK (
    chat_id IN (SELECT id FROM conthunt.chats
                WHERE user_id = current_setting('app.user_id', true)::uuid)
  );
