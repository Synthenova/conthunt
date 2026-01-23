-- Allow service role to read usage limits (needed for API summaries)
SET search_path = conthunt, public;

DROP POLICY IF EXISTS limits_select_service ON usage_limits;
CREATE POLICY limits_select_service ON usage_limits
FOR SELECT TO conthunt_service
USING (true);
