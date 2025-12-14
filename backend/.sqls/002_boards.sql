SET search_path = conthunt, public;

-- Explicitly specify schema to avoid resolution errors
CREATE TABLE conthunt.boards (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES conthunt.users(id) ON DELETE CASCADE,
  name         text NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE conthunt.board_items (
  board_id        uuid NOT NULL REFERENCES conthunt.boards(id) ON DELETE CASCADE,
  content_item_id uuid NOT NULL REFERENCES conthunt.content_items(id) ON DELETE CASCADE,
  added_at        timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (board_id, content_item_id)
);

CREATE INDEX idx_boards_user ON conthunt.boards(user_id);
CREATE INDEX idx_board_items_content ON conthunt.board_items(content_item_id);

---

GRANT SELECT, INSERT, UPDATE, DELETE ON conthunt.boards TO conthunt_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON conthunt.board_items TO conthunt_app;

---

ALTER TABLE conthunt.boards FORCE ROW LEVEL SECURITY;
ALTER TABLE conthunt.board_items FORCE ROW LEVEL SECURITY;

---

-- Policies for boards (fully qualified)
CREATE POLICY boards_select_own
  ON conthunt.boards
  FOR SELECT
  TO conthunt_app
  USING (user_id = current_setting('app.user_id', true)::uuid);

CREATE POLICY boards_insert_own
  ON conthunt.boards
  FOR INSERT
  TO conthunt_app
  WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

CREATE POLICY boards_update_own
  ON conthunt.boards
  FOR UPDATE
  TO conthunt_app
  USING (user_id = current_setting('app.user_id', true)::uuid)
  WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

CREATE POLICY boards_delete_own
  ON conthunt.boards
  FOR DELETE
  TO conthunt_app
  USING (user_id = current_setting('app.user_id', true)::uuid);

-- Policies for board_items (fully qualified)
CREATE POLICY board_items_select_own
  ON conthunt.board_items
  FOR SELECT
  TO conthunt_app
  USING (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );

CREATE POLICY board_items_insert_own
  ON conthunt.board_items
  FOR INSERT
  TO conthunt_app
  WITH CHECK (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );

CREATE POLICY board_items_delete_own
  ON conthunt.board_items
  FOR DELETE
  TO conthunt_app
  USING (
    board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid)
  );
