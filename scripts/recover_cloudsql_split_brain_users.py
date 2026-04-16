#!/usr/bin/env python3
import argparse
import asyncio
import re
from pathlib import Path

import asyncpg


USER_IDS = [
    "787b09aa-3a72-4a0f-9012-43feb7f66a26",
    "b718080f-e9dc-4dcb-866b-ee514b06786b",
    "334f8aa7-b6be-46d1-ad3c-5d0ecdf32080",
    "12b66c0c-a375-4c4c-9d9e-49e1186def98",
    "3314fc7a-a44b-4d38-b28e-462d721e32b6",
    "d2627be3-a6ee-4dea-8cdb-2a70e22db2c6",
    "c1ed16bf-bb71-47a3-8f24-f59f16bd790b",
]

TABLE_SPECS = [
    {
        "table": "users",
        "where_col": "id",
        "columns": [
            "id",
            "firebase_uid",
            "created_at",
            "role",
            "current_period_start",
            "dodo_customer_id",
            "credit_period_start",
            "timezone",
            "whop_user_id",
        ],
    },
    {
        "table": "user_onboarding_progress",
        "where_col": "user_id",
        "columns": [
            "id",
            "user_id",
            "flow_id",
            "current_step",
            "status",
            "started_at",
            "completed_at",
            "updated_at",
            "restart_count",
        ],
    },
    {
        "table": "user_streaks",
        "where_col": "user_id",
        "columns": [
            "id",
            "user_id",
            "streak_type_id",
            "current_streak",
            "longest_streak",
            "last_activity_date",
            "last_action_at",
            "created_at",
            "updated_at",
        ],
    },
    {
        "table": "user_streak_days",
        "where_col": "user_id",
        "columns": [
            "id",
            "user_id",
            "streak_type_id",
            "activity_date",
            "first_activity_at",
            "created_at",
        ],
    },
    {
        "table": "user_analysis_access",
        "where_col": "user_id",
        "columns": [
            "id",
            "user_id",
            "media_asset_id",
            "created_at",
        ],
    },
    {
        "table": "usage_logs",
        "where_col": "user_id",
        "columns": [
            "id",
            "user_id",
            "feature",
            "quantity",
            "context",
            "created_at",
        ],
    },
    {
        "table": "billing_subscriptions",
        "where_col": "user_id",
        "columns": [
            "id",
            "user_id",
            "subscription_id",
            "customer_id",
            "product_id",
            "status",
            "cancel_at_period_end",
            "current_period_start",
            "current_period_end",
            "last_webhook_ts",
            "created_at",
            "updated_at",
            "provider",
            "effective_product_id",
            "billing_state",
            "payment_status",
            "access_status",
            "entitlement_status",
            "pending_change_type",
            "pending_target_product_id",
            "pending_effective_at",
            "last_payment_status",
            "last_paid_at",
            "version",
            "metadata",
            # Present in Neon but absent in Cloud SQL; keep null on import.
            "trial_period_days",
            "trial_ends_at",
            "first_charge_at",
        ],
        "source_columns": [
            "id",
            "user_id",
            "subscription_id",
            "customer_id",
            "product_id",
            "status",
            "cancel_at_period_end",
            "current_period_start",
            "current_period_end",
            "last_webhook_ts",
            "created_at",
            "updated_at",
            "provider",
            "effective_product_id",
            "billing_state",
            "payment_status",
            "access_status",
            "entitlement_status",
            "pending_change_type",
            "pending_target_product_id",
            "pending_effective_at",
            "last_payment_status",
            "last_paid_at",
            "version",
            "metadata",
        ],
    },
]


def load_neon_url() -> str:
    env_text = Path("backend/.env.prod").read_text()
    match = re.search(r"^DATABASE_URL=(.+)$", env_text, re.M)
    if not match:
        raise RuntimeError("DATABASE_URL not found in backend/.env.prod")
    return match.group(1).strip().strip('"').replace("postgresql+asyncpg://", "postgresql://", 1)


async def connect_cloudsql() -> asyncpg.Connection:
    return await asyncpg.connect(
        user="conthunt_app",
        password="Wryip!357911",
        database="postgres",
        host="35.222.84.78",
        port=5432,
        ssl="require",
        statement_cache_size=0,
    )


async def connect_neon() -> asyncpg.Connection:
    return await asyncpg.connect(load_neon_url(), statement_cache_size=0)


async def fetch_rows(conn: asyncpg.Connection, spec: dict) -> list[asyncpg.Record]:
    source_columns = spec.get("source_columns", spec["columns"])
    sql = f"""
        select {", ".join(source_columns)}
        from conthunt.{spec["table"]}
        where {spec["where_col"]} = any($1::uuid[])
        order by 1
    """
    return await conn.fetch(sql, USER_IDS)


async def insert_rows(conn: asyncpg.Connection, spec: dict, rows: list[asyncpg.Record]) -> int:
    if not rows:
        return 0

    insert_columns = spec["columns"]
    source_columns = spec.get("source_columns", insert_columns)
    placeholders = ", ".join(f"${i}" for i in range(1, len(insert_columns) + 1))
    sql = f"""
        insert into conthunt.{spec["table"]} ({", ".join(insert_columns)})
        values ({placeholders})
        on conflict do nothing
    """

    values_list = []
    for row in rows:
        values = [row[col] for col in source_columns]
        if spec["table"] == "billing_subscriptions":
            values.extend([None, None, None])
        values_list.append(tuple(values))

    await conn.executemany(sql, values_list)
    return len(values_list)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Recover split-brain users from Cloud SQL into Neon.")
    parser.add_argument("--execute", action="store_true", help="Apply inserts to Neon. Default is dry-run.")
    args = parser.parse_args()

    cloud = await connect_cloudsql()
    neon = await connect_neon()
    try:
        fetched = {}
        for spec in TABLE_SPECS:
            fetched[spec["table"]] = await fetch_rows(cloud, spec)

        print("Planned row copy counts:", flush=True)
        for spec in TABLE_SPECS:
            print(f"{spec['table']}: {len(fetched[spec['table']])}", flush=True)

        if not args.execute:
            return

        async with neon.transaction():
            print("\nApplying inserts to Neon:", flush=True)
            for spec in TABLE_SPECS:
                inserted = await insert_rows(neon, spec, fetched[spec["table"]])
                print(f"{spec['table']}: inserted {inserted}", flush=True)
    finally:
        await cloud.close()
        await neon.close()


if __name__ == "__main__":
    asyncio.run(main())
