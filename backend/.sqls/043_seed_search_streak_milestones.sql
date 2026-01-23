-- Seed search-only streak milestones for all roles
SET search_path = conthunt, public;

-- Ensure search streak type exists
INSERT INTO streak_types (slug, label) VALUES
('search', 'Search')
ON CONFLICT (slug) DO UPDATE
SET label = EXCLUDED.label;

WITH st AS (
    SELECT id FROM streak_types WHERE slug = 'search'
),
roles AS (
    SELECT unnest(ARRAY['free', 'creator', 'pro_research']) AS role
),
milestones AS (
    SELECT *
    FROM (VALUES
        (3,   0,  10, '10 Searches'),
        (10, 50,   0, '50 Credits'),
        (50, 100, 10, '100 Credits + 10 Searches'),
        (100, 200, 20, '200 Credits + 20 Searches'),
        (365, 500, 50, '500 Credits + 50 Searches')
    ) AS m(days_required, reward_credits, reward_feature_amount, reward_description)
)
INSERT INTO streak_milestones (
    role,
    streak_type_id,
    days_required,
    reward_description,
    icon_name,
    reward_feature,
    reward_credits,
    reward_feature_amount
)
SELECT
    roles.role,
    st.id,
    milestones.days_required,
    milestones.reward_description,
    'gift',
    CASE WHEN milestones.reward_feature_amount > 0 THEN 'search_query' ELSE NULL END,
    milestones.reward_credits,
    milestones.reward_feature_amount
FROM roles
CROSS JOIN st
CROSS JOIN milestones
ON CONFLICT (role, streak_type_id, days_required) DO UPDATE
SET reward_description = EXCLUDED.reward_description,
    icon_name = EXCLUDED.icon_name,
    reward_feature = EXCLUDED.reward_feature,
    reward_credits = EXCLUDED.reward_credits,
    reward_feature_amount = EXCLUDED.reward_feature_amount;
