"""Backfill persisted trial facts on billing_subscriptions.

Usage:
    APP_ENV=local python scripts/backfill_billing_trials.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import timedelta
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import get_db_connection
from app.services import dodo_client


async def main() -> None:
    await dodo_client.get_products()

    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            SELECT
                subscription_id,
                COALESCE(effective_product_id, product_id) AS effective_product_id,
                current_period_start,
                current_period_end
            FROM billing_subscriptions
            ORDER BY last_webhook_ts DESC
            """)
        )
        rows = result.fetchall()

        updated = 0
        skipped = 0

        for row in rows:
            subscription_id = row[0]
            product_id = row[1]
            current_period_start = row[2]
            current_period_end = row[3]

            product = dodo_client.get_product_by_id(product_id) if product_id else None
            trial_period_days = int((product or {}).get("trial_period_days") or 0)

            trial_ends_at = None
            first_charge_at = None
            if trial_period_days > 0 and current_period_start is not None:
                trial_ends_at = current_period_start + timedelta(days=trial_period_days)
                if current_period_end and current_period_end < trial_ends_at:
                    trial_ends_at = current_period_end
                first_charge_at = trial_ends_at
            elif trial_period_days <= 0:
                trial_period_days = None
            else:
                skipped += 1
                continue

            await conn.execute(
                text("""
                UPDATE billing_subscriptions
                SET trial_period_days = :trial_period_days,
                    trial_ends_at = :trial_ends_at,
                    first_charge_at = :first_charge_at,
                    updated_at = now()
                WHERE subscription_id = :subscription_id
                """),
                {
                    "subscription_id": subscription_id,
                    "trial_period_days": trial_period_days,
                    "trial_ends_at": trial_ends_at,
                    "first_charge_at": first_charge_at,
                },
            )
            updated += 1

    print(
        f"Backfilled billing trial fields for {updated} subscriptions"
        + (f" ({skipped} skipped due to missing current_period_start)" if skipped else "")
    )


if __name__ == "__main__":
    asyncio.run(main())
