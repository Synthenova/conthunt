-- ============================================================
-- Migration 011: Fix RLS Privacy for conthunt_service
-- ============================================================
-- 
-- Problem: 010 created USING(true) policies which bypass user filtering.
-- Solution: Replace with proper user_id checks for user-scoped tables.
-- ============================================================

-- ============================================================
-- SHARED TABLES (Keep USING(true) - no user ownership)
-- ============================================================

-- USERS - service needs full access to authenticate/create
DROP POLICY IF EXISTS users_select_service ON conthunt.users;
DROP POLICY IF EXISTS users_insert_service ON conthunt.users;
DROP POLICY IF EXISTS users_update_service ON conthunt.users;
DROP POLICY IF EXISTS users_delete_service ON conthunt.users;
CREATE POLICY users_all_service ON conthunt.users FOR ALL TO conthunt_service USING (true) WITH CHECK (true);

-- CONTENT_ITEMS - shared cache
DROP POLICY IF EXISTS content_items_select_service ON conthunt.content_items;
DROP POLICY IF EXISTS content_items_insert_service ON conthunt.content_items;
DROP POLICY IF EXISTS content_items_update_service ON conthunt.content_items;
DROP POLICY IF EXISTS content_items_delete_service ON conthunt.content_items;
CREATE POLICY content_items_all_service ON conthunt.content_items FOR ALL TO conthunt_service USING (true) WITH CHECK (true);

-- MEDIA_ASSETS - shared
DROP POLICY IF EXISTS media_assets_select_service ON conthunt.media_assets;
DROP POLICY IF EXISTS media_assets_insert_service ON conthunt.media_assets;
DROP POLICY IF EXISTS media_assets_update_service ON conthunt.media_assets;
DROP POLICY IF EXISTS media_assets_delete_service ON conthunt.media_assets;
CREATE POLICY media_assets_all_service ON conthunt.media_assets FOR ALL TO conthunt_service USING (true) WITH CHECK (true);

-- TWELVELABS_ASSETS - shared
DROP POLICY IF EXISTS twelvelabs_assets_select_service ON conthunt.twelvelabs_assets;
DROP POLICY IF EXISTS twelvelabs_assets_insert_service ON conthunt.twelvelabs_assets;
DROP POLICY IF EXISTS twelvelabs_assets_update_service ON conthunt.twelvelabs_assets;
DROP POLICY IF EXISTS twelvelabs_assets_delete_service ON conthunt.twelvelabs_assets;
CREATE POLICY twelvelabs_assets_all_service ON conthunt.twelvelabs_assets FOR ALL TO conthunt_service USING (true) WITH CHECK (true);

-- VIDEO_ANALYSES - shared cache
DROP POLICY IF EXISTS video_analyses_select_service ON conthunt.video_analyses;
DROP POLICY IF EXISTS video_analyses_insert_service ON conthunt.video_analyses;
DROP POLICY IF EXISTS video_analyses_update_service ON conthunt.video_analyses;
DROP POLICY IF EXISTS video_analyses_delete_service ON conthunt.video_analyses;
CREATE POLICY video_analyses_all_service ON conthunt.video_analyses FOR ALL TO conthunt_service USING (true) WITH CHECK (true);

-- ============================================================
-- USER-SCOPED TABLES (Filter by app.user_id session variable)
-- ============================================================

-- SEARCHES
DROP POLICY IF EXISTS searches_select_service ON conthunt.searches;
DROP POLICY IF EXISTS searches_insert_service ON conthunt.searches;
DROP POLICY IF EXISTS searches_update_service ON conthunt.searches;
DROP POLICY IF EXISTS searches_delete_service ON conthunt.searches;
CREATE POLICY searches_select_service ON conthunt.searches FOR SELECT TO conthunt_service 
  USING (user_id = current_setting('app.user_id', true)::uuid);
CREATE POLICY searches_insert_service ON conthunt.searches FOR INSERT TO conthunt_service 
  WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
CREATE POLICY searches_update_service ON conthunt.searches FOR UPDATE TO conthunt_service 
  USING (user_id = current_setting('app.user_id', true)::uuid);
CREATE POLICY searches_delete_service ON conthunt.searches FOR DELETE TO conthunt_service 
  USING (user_id = current_setting('app.user_id', true)::uuid);

-- PLATFORM_CALLS (via search ownership)
DROP POLICY IF EXISTS platform_calls_select_service ON conthunt.platform_calls;
DROP POLICY IF EXISTS platform_calls_insert_service ON conthunt.platform_calls;
DROP POLICY IF EXISTS platform_calls_update_service ON conthunt.platform_calls;
DROP POLICY IF EXISTS platform_calls_delete_service ON conthunt.platform_calls;
CREATE POLICY platform_calls_select_service ON conthunt.platform_calls FOR SELECT TO conthunt_service 
  USING (search_id IN (SELECT id FROM conthunt.searches WHERE user_id = current_setting('app.user_id', true)::uuid));
CREATE POLICY platform_calls_insert_service ON conthunt.platform_calls FOR INSERT TO conthunt_service 
  WITH CHECK (search_id IN (SELECT id FROM conthunt.searches WHERE user_id = current_setting('app.user_id', true)::uuid));
CREATE POLICY platform_calls_update_service ON conthunt.platform_calls FOR UPDATE TO conthunt_service 
  USING (search_id IN (SELECT id FROM conthunt.searches WHERE user_id = current_setting('app.user_id', true)::uuid));
CREATE POLICY platform_calls_delete_service ON conthunt.platform_calls FOR DELETE TO conthunt_service 
  USING (search_id IN (SELECT id FROM conthunt.searches WHERE user_id = current_setting('app.user_id', true)::uuid));

-- SEARCH_RESULTS (via search ownership)
DROP POLICY IF EXISTS search_results_select_service ON conthunt.search_results;
DROP POLICY IF EXISTS search_results_insert_service ON conthunt.search_results;
DROP POLICY IF EXISTS search_results_update_service ON conthunt.search_results;
DROP POLICY IF EXISTS search_results_delete_service ON conthunt.search_results;
CREATE POLICY search_results_select_service ON conthunt.search_results FOR SELECT TO conthunt_service 
  USING (search_id IN (SELECT id FROM conthunt.searches WHERE user_id = current_setting('app.user_id', true)::uuid));
CREATE POLICY search_results_insert_service ON conthunt.search_results FOR INSERT TO conthunt_service 
  WITH CHECK (search_id IN (SELECT id FROM conthunt.searches WHERE user_id = current_setting('app.user_id', true)::uuid));
CREATE POLICY search_results_delete_service ON conthunt.search_results FOR DELETE TO conthunt_service 
  USING (search_id IN (SELECT id FROM conthunt.searches WHERE user_id = current_setting('app.user_id', true)::uuid));

-- BOARDS
DROP POLICY IF EXISTS boards_select_service ON conthunt.boards;
DROP POLICY IF EXISTS boards_insert_service ON conthunt.boards;
DROP POLICY IF EXISTS boards_update_service ON conthunt.boards;
DROP POLICY IF EXISTS boards_delete_service ON conthunt.boards;
CREATE POLICY boards_select_service ON conthunt.boards FOR SELECT TO conthunt_service 
  USING (user_id = current_setting('app.user_id', true)::uuid);
CREATE POLICY boards_insert_service ON conthunt.boards FOR INSERT TO conthunt_service 
  WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
CREATE POLICY boards_update_service ON conthunt.boards FOR UPDATE TO conthunt_service 
  USING (user_id = current_setting('app.user_id', true)::uuid);
CREATE POLICY boards_delete_service ON conthunt.boards FOR DELETE TO conthunt_service 
  USING (user_id = current_setting('app.user_id', true)::uuid);

-- BOARD_ITEMS (via board ownership)
DROP POLICY IF EXISTS board_items_select_service ON conthunt.board_items;
DROP POLICY IF EXISTS board_items_insert_service ON conthunt.board_items;
DROP POLICY IF EXISTS board_items_update_service ON conthunt.board_items;
DROP POLICY IF EXISTS board_items_delete_service ON conthunt.board_items;
CREATE POLICY board_items_select_service ON conthunt.board_items FOR SELECT TO conthunt_service 
  USING (board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid));
CREATE POLICY board_items_insert_service ON conthunt.board_items FOR INSERT TO conthunt_service 
  WITH CHECK (board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid));
CREATE POLICY board_items_delete_service ON conthunt.board_items FOR DELETE TO conthunt_service 
  USING (board_id IN (SELECT id FROM conthunt.boards WHERE user_id = current_setting('app.user_id', true)::uuid));

-- CHATS
DROP POLICY IF EXISTS chats_select_service ON conthunt.chats;
DROP POLICY IF EXISTS chats_insert_service ON conthunt.chats;
DROP POLICY IF EXISTS chats_update_service ON conthunt.chats;
DROP POLICY IF EXISTS chats_delete_service ON conthunt.chats;
CREATE POLICY chats_select_service ON conthunt.chats FOR SELECT TO conthunt_service 
  USING (user_id = current_setting('app.user_id', true)::uuid);
CREATE POLICY chats_insert_service ON conthunt.chats FOR INSERT TO conthunt_service 
  WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
CREATE POLICY chats_update_service ON conthunt.chats FOR UPDATE TO conthunt_service 
  USING (user_id = current_setting('app.user_id', true)::uuid);
CREATE POLICY chats_delete_service ON conthunt.chats FOR DELETE TO conthunt_service 
  USING (user_id = current_setting('app.user_id', true)::uuid);
