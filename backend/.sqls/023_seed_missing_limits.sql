SET search_path = conthunt, public;

-- Ensure all plan limits are seeded
-- This fixes the issue where limits might be missing if 017 was run before seed data was added

-- 1. Gemini Analysis Limits
INSERT INTO plan_limits (plan_role, feature, period, limit_count) VALUES
('free', 'gemini_analysis', 'daily', 20),
('creator', 'gemini_analysis', 'daily', 50),
('pro_research', 'gemini_analysis', 'daily', 500)
ON CONFLICT (plan_role, feature, period) 
DO UPDATE SET limit_count = EXCLUDED.limit_count;

-- 2. Search Query Limits
INSERT INTO plan_limits (plan_role, feature, period, limit_count) VALUES
('free', 'search_query', 'daily', 20),
('creator', 'search_query', 'daily', 100),
('pro_research', 'search_query', 'daily', 1000)
ON CONFLICT (plan_role, feature, period) 
DO UPDATE SET limit_count = EXCLUDED.limit_count;
