SET search_path = conthunt, public;

CREATE TABLE conthunt.board_insights (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  board_id uuid NOT NULL REFERENCES conthunt.boards(id) ON DELETE CASCADE UNIQUE,
  status text NOT NULL DEFAULT 'processing',
  insights_result jsonb NOT NULL DEFAULT '{}'::jsonb,
  error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  last_completed_at timestamptz
);

CREATE INDEX idx_board_insights_board_status
  ON conthunt.board_insights(board_id, status);

GRANT SELECT, INSERT, UPDATE, DELETE ON conthunt.board_insights TO conthunt_app;

ALTER TABLE conthunt.board_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE conthunt.board_insights FORCE ROW LEVEL SECURITY;

CREATE POLICY board_insights_select_own
  ON conthunt.board_insights
  FOR SELECT
  TO conthunt_app
  USING (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );

CREATE POLICY board_insights_insert_own
  ON conthunt.board_insights
  FOR INSERT
  TO conthunt_app
  WITH CHECK (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );

CREATE POLICY board_insights_update_own
  ON conthunt.board_insights
  FOR UPDATE
  TO conthunt_app
  USING (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  )
  WITH CHECK (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );

CREATE POLICY board_insights_delete_own
  ON conthunt.board_insights
  FOR DELETE
  TO conthunt_app
  USING (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );

CREATE POLICY board_insights_select_service
  ON conthunt.board_insights
  FOR SELECT
  TO conthunt_service
  USING (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );

CREATE POLICY board_insights_insert_service
  ON conthunt.board_insights
  FOR INSERT
  TO conthunt_service
  WITH CHECK (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );

CREATE POLICY board_insights_update_service
  ON conthunt.board_insights
  FOR UPDATE
  TO conthunt_service
  USING (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  )
  WITH CHECK (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );

CREATE POLICY board_insights_delete_service
  ON conthunt.board_insights
  FOR DELETE
  TO conthunt_service
  USING (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );
