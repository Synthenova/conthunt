"""Remove free plan entitlements now that paid plans are required for search.

Revision ID: 0007_remove_free_plan_entitlements
Revises: 0006_seed_reference_data
Create Date: 2026-04-11
"""

from __future__ import annotations

import os

from alembic import op


revision = "0007_remove_free_plan_entitlements"
down_revision = "0006_seed_reference_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        UPDATE {schema}.usage_limits
        SET limit_count = 0,
            updated_at = now()
        WHERE plan_role = 'free'
          AND feature = 'search_query'
          AND period = 'monthly';

        DELETE FROM {schema}.streak_milestones
        WHERE role = 'free';
        """.strip()
    )


def downgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        UPDATE {schema}.usage_limits
        SET limit_count = 10,
            updated_at = now()
        WHERE plan_role = 'free'
          AND feature = 'search_query'
          AND period = 'monthly';

        INSERT INTO {schema}.streak_milestones (
            id,
            streak_type_id,
            role,
            days_required,
            reward_description,
            icon_name,
            reward_feature,
            reward_credits,
            reward_feature_amount,
            created_at
        )
        SELECT
            milestone.id,
            streak_type.id,
            milestone.role,
            milestone.days_required,
            milestone.reward_description,
            milestone.icon_name,
            milestone.reward_feature,
            milestone.reward_credits,
            milestone.reward_feature_amount,
            milestone.created_at::timestamptz
        FROM (
            VALUES
                ('6f5dff00-8aeb-4d25-9595-c6713501e780'::uuid, 'free', 3, '10 Searches', 'Search', 'search_query', 0, 10, '2026-01-20 01:17:14.805011+00'::timestamptz),
                ('0cb91077-7804-4144-8655-b71f224eef0f'::uuid, 'free', 10, '50 Credits', 'Coins', NULL, 50, 0, '2026-01-20 01:17:14.805011+00'::timestamptz),
                ('85bf370c-bc4f-4469-a098-a4eff15efc84'::uuid, 'free', 50, '100 Credits + 10 Searches', 'Award', 'search_query', 100, 10, '2026-01-20 01:17:14.805011+00'::timestamptz),
                ('21dcb280-b94c-4551-87f1-f02e48c95f4b'::uuid, 'free', 100, '200 Credits + 20 Searches', 'Crown', 'search_query', 200, 20, '2026-01-20 01:17:14.805011+00'::timestamptz),
                ('410c6745-4561-4bb0-8737-113d6f5cbad5'::uuid, 'free', 365, '500 Credits + 50 Searches', 'Sparkles', 'search_query', 500, 50, '2026-01-20 01:17:14.805011+00'::timestamptz)
        ) AS milestone(
            id,
            role,
            days_required,
            reward_description,
            icon_name,
            reward_feature,
            reward_credits,
            reward_feature_amount,
            created_at
        )
        JOIN {schema}.streak_types AS streak_type
          ON streak_type.slug = 'search'
        ON CONFLICT (role, streak_type_id, days_required) DO UPDATE
        SET
            reward_description = EXCLUDED.reward_description,
            icon_name = EXCLUDED.icon_name,
            reward_feature = EXCLUDED.reward_feature,
            reward_credits = EXCLUDED.reward_credits,
            reward_feature_amount = EXCLUDED.reward_feature_amount;
        """.strip()
    )
