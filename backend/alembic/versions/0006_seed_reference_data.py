"""Seed reference and config data required by the application.

Revision ID: 0006_seed_reference_data
Revises: 0005_drop_legacy_billing_tables
Create Date: 2026-04-06
"""

from __future__ import annotations

import os

from alembic import op


revision = "0006_seed_reference_data"
down_revision = "0005_drop_legacy_billing_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        SET search_path TO {schema}, public;

        INSERT INTO {schema}.feature_config (id, feature, credit_cost, created_at)
        VALUES
            ('c78dea23-0164-48a7-8740-b1285d3b582a', 'search_query', 1, '2026-01-11 09:29:02.552484+00'),
            ('a5fb53b9-e095-455c-a465-5c0b2675c7ef', 'video_analysis', 2, '2026-01-11 09:29:02.552484+00'),
            ('dda559e1-36f9-4f50-a52c-d03377532f7f', 'index_video', 5, '2026-01-11 09:29:02.552484+00')
        ON CONFLICT (feature) DO UPDATE
        SET credit_cost = EXCLUDED.credit_cost;

        INSERT INTO {schema}.usage_limits (
            id,
            plan_role,
            feature,
            period,
            limit_count,
            created_at,
            updated_at
        )
        VALUES
            (
                '407a685e-1ba5-4479-a0d5-7e47cf7ef026',
                'creator',
                'search_query',
                'monthly',
                50,
                '2026-01-19 22:44:10.733166+00',
                '2026-01-22 18:59:14.788188+00'
            ),
            (
                'aea42ee2-4fa3-46ed-8d11-c7802aaa6d93',
                'free',
                'search_query',
                'monthly',
                10,
                '2026-01-19 22:44:10.733166+00',
                '2026-01-22 18:59:14.788188+00'
            ),
            (
                '822ed99e-c7ba-4035-bac8-9cd6415ed2e3',
                'pro_research',
                'search_query',
                'monthly',
                300,
                '2026-01-19 22:44:10.733166+00',
                '2026-01-22 18:59:14.788188+00'
            )
        ON CONFLICT (plan_role, feature, period) DO UPDATE
        SET
            limit_count = EXCLUDED.limit_count,
            updated_at = EXCLUDED.updated_at;

        INSERT INTO {schema}.streak_types (id, slug, label, created_at)
        VALUES
            ('b8ed050b-459e-4d92-b5b3-e6ff0fe4fcb0', 'open', 'App Open', '2026-01-19 14:10:08.226694+00'),
            ('ad0e9299-9028-4b95-b96b-101f892d01c7', 'analysis', 'Analysis', '2026-01-19 14:10:08.226694+00'),
            ('c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25', 'search', 'Search', '2026-01-19 14:10:08.226694+00')
        ON CONFLICT (slug) DO UPDATE
        SET label = EXCLUDED.label;

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
        VALUES
            (
                '6f5dff00-8aeb-4d25-9595-c6713501e780',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'free',
                3,
                '10 Searches',
                'Search',
                'search_query',
                0,
                10,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                '68166f8d-42fb-4337-9088-59ba96d3ee82',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'creator',
                3,
                '10 Searches',
                'Search',
                'search_query',
                0,
                10,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                'fc12469d-7ea5-47d5-bd71-d4e3e77043b6',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'pro_research',
                3,
                '10 Searches',
                'Search',
                'search_query',
                0,
                10,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                '0cb91077-7804-4144-8655-b71f224eef0f',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'free',
                10,
                '50 Credits',
                'Coins',
                NULL,
                50,
                0,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                '8b7f8af9-56d3-43e7-803f-9769a047dd75',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'creator',
                10,
                '50 Credits',
                'Coins',
                NULL,
                50,
                0,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                '7a5bc16b-d822-44b5-88e9-e968f7a01993',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'pro_research',
                10,
                '50 Credits',
                'Coins',
                NULL,
                50,
                0,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                '85bf370c-bc4f-4469-a098-a4eff15efc84',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'free',
                50,
                '100 Credits + 10 Searches',
                'Award',
                'search_query',
                100,
                10,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                'a4fb7e10-cdd3-410d-859d-7e65a84cdb1b',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'creator',
                50,
                '100 Credits + 10 Searches',
                'Award',
                'search_query',
                100,
                10,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                'b0efaadd-2d26-44d9-8ffc-ab6589dc9fa2',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'pro_research',
                50,
                '100 Credits + 10 Searches',
                'Award',
                'search_query',
                100,
                10,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                '21dcb280-b94c-4551-87f1-f02e48c95f4b',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'free',
                100,
                '200 Credits + 20 Searches',
                'Crown',
                'search_query',
                200,
                20,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                '54c5cae9-ad60-48ee-9352-b9744fb14ce5',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'creator',
                100,
                '200 Credits + 20 Searches',
                'Crown',
                'search_query',
                200,
                20,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                'fe501907-718b-4e8d-a77c-819bfb9e11f2',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'pro_research',
                100,
                '200 Credits + 20 Searches',
                'Crown',
                'search_query',
                200,
                20,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                '410c6745-4561-4bb0-8737-113d6f5cbad5',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'free',
                365,
                '500 Credits + 50 Searches',
                'Sparkles',
                'search_query',
                500,
                50,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                '8a9d7c32-17d9-4347-bd48-776082d5ff4c',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'creator',
                365,
                '500 Credits + 50 Searches',
                'Sparkles',
                'search_query',
                500,
                50,
                '2026-01-20 01:17:14.805011+00'
            ),
            (
                'a98e017c-c405-4a87-9fd9-abc8e37941da',
                'c8bfb77c-4eb1-4aa5-a16d-866dbb75ae25',
                'pro_research',
                365,
                '500 Credits + 50 Searches',
                'Sparkles',
                'search_query',
                500,
                50,
                '2026-01-20 01:17:14.805011+00'
            )
        ON CONFLICT (role, streak_type_id, days_required) DO UPDATE
        SET
            reward_description = EXCLUDED.reward_description,
            icon_name = EXCLUDED.icon_name,
            reward_feature = EXCLUDED.reward_feature,
            reward_credits = EXCLUDED.reward_credits,
            reward_feature_amount = EXCLUDED.reward_feature_amount;
        """.strip()
    )


def downgrade() -> None:
    schema = os.getenv("DB_SCHEMA", "conthunt")
    op.execute(
        f"""
        SET search_path TO {schema}, public;

        DELETE FROM {schema}.streak_milestones
        WHERE id IN (
            '6f5dff00-8aeb-4d25-9595-c6713501e780',
            '68166f8d-42fb-4337-9088-59ba96d3ee82',
            'fc12469d-7ea5-47d5-bd71-d4e3e77043b6',
            '0cb91077-7804-4144-8655-b71f224eef0f',
            '8b7f8af9-56d3-43e7-803f-9769a047dd75',
            '7a5bc16b-d822-44b5-88e9-e968f7a01993',
            '85bf370c-bc4f-4469-a098-a4eff15efc84',
            'a4fb7e10-cdd3-410d-859d-7e65a84cdb1b',
            'b0efaadd-2d26-44d9-8ffc-ab6589dc9fa2',
            '21dcb280-b94c-4551-87f1-f02e48c95f4b',
            '54c5cae9-ad60-48ee-9352-b9744fb14ce5',
            'fe501907-718b-4e8d-a77c-819bfb9e11f2',
            '410c6745-4561-4bb0-8737-113d6f5cbad5',
            '8a9d7c32-17d9-4347-bd48-776082d5ff4c',
            'a98e017c-c405-4a87-9fd9-abc8e37941da'
        );

        DELETE FROM {schema}.streak_types
        WHERE slug IN ('open', 'analysis', 'search');

        DELETE FROM {schema}.usage_limits
        WHERE
            feature = 'search_query'
            AND period = 'monthly'
            AND plan_role IN ('free', 'creator', 'pro_research');

        DELETE FROM {schema}.feature_config
        WHERE feature IN ('search_query', 'video_analysis', 'index_video');
        """.strip()
    )
