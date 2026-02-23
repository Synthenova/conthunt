"""Recompute billing winner state for users from billing_subscriptions."""
import asyncio
import sys
from uuid import UUID
from pathlib import Path

# Allow running script directly: `python scripts/recompute_billing_winners.py`
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import text

from app.db.session import init_db, get_db_connection
from app.services.billing_service import recompute_user_billing_winner


async def main() -> None:
    await init_db()
    target_user_id = sys.argv[1] if len(sys.argv) > 1 else None

    if target_user_id:
        summary = await recompute_user_billing_winner(UUID(target_user_id))
        print(summary)
        return

    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            SELECT DISTINCT user_id
            FROM billing_subscriptions
            ORDER BY user_id
            """)
        )
        user_ids = [row[0] for row in result.fetchall()]

    print(f"Recomputing billing winner for {len(user_ids)} users...")
    for user_id in user_ids:
        summary = await recompute_user_billing_winner(user_id)
        print(summary)


if __name__ == "__main__":
    asyncio.run(main())
