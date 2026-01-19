-- Usage limits (monthly) - search_query only
SET search_path = conthunt, public;

CREATE TABLE IF NOT EXISTS usage_limits (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_role text NOT NULL,
    feature text NOT NULL,
    period text NOT NULL CHECK (period IN ('hourly', 'daily', 'monthly', 'yearly', 'total')),
    limit_count int NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(plan_role, feature, period)
);

INSERT INTO usage_limits (plan_role, feature, period, limit_count) VALUES
('free', 'search_query', 'monthly', 50),
('creator', 'search_query', 'monthly', 150),
('pro_research', 'search_query', 'monthly', 500)
ON CONFLICT (plan_role, feature, period)
DO UPDATE SET limit_count = EXCLUDED.limit_count;

ALTER TABLE usage_limits ENABLE ROW LEVEL SECURITY;

GRANT SELECT ON usage_limits TO conthunt_app;
GRANT ALL ON usage_limits TO conthunt_service;

DROP POLICY IF EXISTS limits_select_all ON usage_limits;
CREATE POLICY limits_select_all ON usage_limits FOR SELECT TO conthunt_app
USING (true);
