-- Streak types + milestones seed (per role + type)
SET search_path = conthunt, public;

INSERT INTO streak_types (slug, label) VALUES
('open', 'App Open'),
('search', 'Search'),
('analysis', 'Analysis')
ON CONFLICT (slug) DO UPDATE
SET label = EXCLUDED.label;

WITH roles AS (
    SELECT unnest(ARRAY['free', 'creator', 'pro_research']) AS role
),
milestones AS (
    SELECT *
    FROM (VALUES
        (10,  '500 Credits', 'gift'),
        (50,  '2,000 Credits + T-Shirt', 'shirt'),
        (100, '5,000 Credits + Hoodie', 'package'),
        (365, 'Exclusive NYC Event Invite', 'plane')
    ) AS m(days_required, reward_description, icon_name)
)
INSERT INTO streak_milestones (role, streak_type_id, days_required, reward_description, icon_name)
SELECT
    roles.role,
    st.id,
    milestones.days_required,
    milestones.reward_description,
    milestones.icon_name
FROM roles
CROSS JOIN streak_types st
CROSS JOIN milestones
ON CONFLICT (role, streak_type_id, days_required) DO UPDATE
SET reward_description = EXCLUDED.reward_description,
    icon_name = EXCLUDED.icon_name;
