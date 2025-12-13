SET search_path = conthunt, public;

CREATE TABLE users (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  firebase_uid text UNIQUE NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE searches (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  query       text NOT NULL,
  inputs      jsonb NOT NULL,
  search_hash text NOT NULL,
  mode        text NOT NULL DEFAULT 'prefer_cache',
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_searches_user_created ON searches (user_id, created_at DESC);
CREATE INDEX idx_searches_user_hash ON searches (user_id, search_hash);
CREATE INDEX idx_searches_inputs_gin ON searches USING GIN (inputs jsonb_path_ops);

CREATE TABLE platform_calls (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  search_id        uuid NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
  platform         text NOT NULL,
  request_params   jsonb NOT NULL,
  response_gcs_uri text,
  response_meta    jsonb NOT NULL DEFAULT '{}'::jsonb,
  next_cursor      jsonb,
  success          boolean NOT NULL DEFAULT false,
  http_status      int,
  error            text,
  duration_ms      int,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE content_items (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform       text NOT NULL,
  external_id    text NOT NULL,
  content_type   text NOT NULL,
  canonical_url  text,
  title          text,
  primary_text   text,
  published_at   timestamptz,
  creator_handle text,
  metrics        jsonb NOT NULL DEFAULT '{}'::jsonb,
  payload        jsonb NOT NULL,
  raw_gcs_uri    text,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE(platform, external_id)
);

CREATE TABLE search_results (
  search_id       uuid NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
  content_item_id uuid NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
  platform        text NOT NULL,
  rank            int NOT NULL,
  PRIMARY KEY (search_id, content_item_id)
);

CREATE TABLE media_assets (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_item_id uuid NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
  asset_type      text NOT NULL,
  source_url      text NOT NULL,
  source_url_list jsonb,
  gcs_uri         text,
  sha256          text,
  mime_type      text,
  bytes           bigint,
  width           int,
  height          int,
  duration_ms     int,
  status          text NOT NULL DEFAULT 'pending',
  error           text,
  created_at      timestamptz NOT NULL DEFAULT now()
);


---

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA conthunt TO conthunt_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA conthunt TO conthunt_app;

-- Future proof: for tables you create later
ALTER DEFAULT PRIVILEGES IN SCHEMA conthunt
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO conthunt_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA conthunt
GRANT USAGE, SELECT ON SEQUENCES TO conthunt_app;


---

ALTER TABLE conthunt.searches FORCE ROW LEVEL SECURITY;
ALTER TABLE conthunt.platform_calls FORCE ROW LEVEL SECURITY;
ALTER TABLE conthunt.search_results FORCE ROW LEVEL SECURITY;

---

CREATE POLICY searches_select_own
  ON conthunt.searches
  FOR SELECT
  TO conthunt_app
  USING (user_id = current_setting('app.user_id', true)::uuid);

CREATE POLICY searches_insert_own
  ON conthunt.searches
  FOR INSERT
  TO conthunt_app
  WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

CREATE POLICY searches_update_own
  ON conthunt.searches
  FOR UPDATE
  TO conthunt_app
  USING (user_id = current_setting('app.user_id', true)::uuid)
  WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
