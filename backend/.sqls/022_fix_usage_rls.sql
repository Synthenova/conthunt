SET search_path = conthunt, public;

-- Fix RLS policies for usage_logs

-- 1. Ensure Service User (conthunt_service) has unrestricted access
-- The backend often runs as this user, so we need explicit policies for it if RLS is enabled.
DROP POLICY IF EXISTS usage_insert_service ON usage_logs;
CREATE POLICY usage_insert_service ON usage_logs 
FOR INSERT TO conthunt_service 
WITH CHECK (true);

DROP POLICY IF EXISTS usage_select_service ON usage_logs;
CREATE POLICY usage_select_service ON usage_logs 
FOR SELECT TO conthunt_service 
USING (true);

DROP POLICY IF EXISTS usage_update_service ON usage_logs;
CREATE POLICY usage_update_service ON usage_logs 
FOR UPDATE TO conthunt_service 
USING (true);

DROP POLICY IF EXISTS usage_delete_service ON usage_logs;
CREATE POLICY usage_delete_service ON usage_logs 
FOR DELETE TO conthunt_service 
USING (true);


-- 2. Ensure Service User can see plan_limits
DROP POLICY IF EXISTS limits_select_service ON plan_limits;
CREATE POLICY limits_select_service ON plan_limits 
FOR SELECT TO conthunt_service 
USING (true);


-- 3. Ensure App User (conthunt_app) works as intended
-- (These were likely correct, but re-stating for safety)
DROP POLICY IF EXISTS usage_insert_own ON usage_logs;
CREATE POLICY usage_insert_own ON usage_logs FOR INSERT TO conthunt_app
WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

DROP POLICY IF EXISTS usage_select_own ON usage_logs;
CREATE POLICY usage_select_own ON usage_logs FOR SELECT TO conthunt_app
USING (user_id = current_setting('app.user_id', true)::uuid);
