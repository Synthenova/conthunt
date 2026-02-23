import asyncio
from app.db.session import init_db
from app.services.billing_service import get_user_subscription
import json

async def main():
    await init_db()
    # Need to get user_id of the user. Wait, let's just get any cancelled subscription from the DB
    from app.db.session import get_db_connection
    from sqlalchemy import text
    
    async with get_db_connection() as conn:
        result = await conn.execute(text("SELECT user_id, status, cancel_at_period_end FROM user_subscriptions WHERE status = 'cancelled' LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"Found user {row.user_id} with status {row.status}, cancel_at_period_end {row.cancel_at_period_end}")
            sub = await get_user_subscription(row.user_id)
            print("get_user_subscription returns:")
            print(json.dumps(sub, default=str, indent=2))
        else:
            print("No cancelled subscriptions found")

if __name__ == "__main__":
    asyncio.run(main())
