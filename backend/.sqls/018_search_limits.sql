SET search_path = conthunt, public;

-- Add search_query limits to plan_limits
INSERT INTO plan_limits (plan_role, feature, period, limit_count) VALUES
('free', 'search_query', 'daily', 10),
('creator', 'search_query', 'daily', 100),
('pro_research', 'search_query', 'daily', 1000)
ON CONFLICT (plan_role, feature, period) 
DO UPDATE SET limit_count = EXCLUDED.limit_count;
