SET search_path = conthunt, public;

-- Track 12Labs indexes we create
-- DEPRECATED: We now use a single index ID from env var.
-- keeping comments for history but removing table creation to match current state
-- CREATE TABLE conthunt.twelvelabs_indexes ( ... );

-- Link content_items to 12Labs assets
CREATE TABLE conthunt.twelvelabs_assets (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_item_id     uuid NOT NULL REFERENCES conthunt.content_items(id) ON DELETE CASCADE UNIQUE,
  index_id            text,                -- 12Labs index ID (static from env)
  asset_id            text NOT NULL,       -- 12Labs asset ID from upload
  indexed_asset_id    text,                -- 12Labs indexed asset ID (after indexing)
  asset_status        text NOT NULL DEFAULT 'pending',  -- pending, processing, ready, failed
  index_status        text,                -- null, pending, queued, indexing, ready, failed
  error               text,
  upload_raw_gcs_uri  text,                -- GCS URI for raw upload response
  index_raw_gcs_uri   text,                -- GCS URI for raw index response
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);

-- Store analysis results (global cache - shared across all users)
CREATE TABLE conthunt.video_analyses (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_item_id     uuid NOT NULL REFERENCES conthunt.content_items(id) ON DELETE CASCADE UNIQUE,
  twelvelabs_asset_id uuid REFERENCES conthunt.twelvelabs_assets(id) ON DELETE SET NULL,
  prompt              text NOT NULL,
  analysis_result     jsonb NOT NULL,
  token_usage         int,
  raw_gcs_uri         text,                -- GCS URI for raw analyze response
  created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_twelvelabs_assets_content ON conthunt.twelvelabs_assets(content_item_id);
CREATE INDEX idx_video_analyses_content ON conthunt.video_analyses(content_item_id);

-- Grant permissions

GRANT SELECT, INSERT, UPDATE, DELETE ON conthunt.twelvelabs_assets TO conthunt_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON conthunt.video_analyses TO conthunt_app;
