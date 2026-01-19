-- Update streak milestone rewards to credits-only
SET search_path = conthunt, public;

UPDATE streak_milestones
SET reward_feature = 'credits',
    reward_amount = CASE days_required
        WHEN 10 THEN 500
        WHEN 50 THEN 2000
        WHEN 100 THEN 5000
        WHEN 365 THEN 10000
        ELSE reward_amount
    END,
    reward_description = CASE days_required
        WHEN 10 THEN '500 Credits'
        WHEN 50 THEN '2,000 Credits'
        WHEN 100 THEN '5,000 Credits'
        WHEN 365 THEN '10,000 Credits'
        ELSE reward_description
    END;
