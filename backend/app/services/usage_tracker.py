import json
from uuid import UUID
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from app.db.session import get_db_connection
from app.core import logger

class UsageTracker:
    async def get_internal_user_id(self, conn, firebase_uid: str) -> Optional[UUID]:
        """Resolves Firebase UID to internal Postgres UUID."""
        result = await conn.execute(
            text("SELECT id FROM users WHERE firebase_uid = :uid"),
            {"uid": firebase_uid}
        )
        row = result.fetchone()
        return row[0] if row else None

    async def record_usage(
        self,
        firebase_uid: str,
        feature: str,
        quantity: int = 1,
        context: Optional[dict] = None
    ) -> None:
        """
        Records usage for a specific feature.
        SAFE: Logs error instead of raising if tracking fails.
        """
        context = context or {}
        try:
            async with get_db_connection() as conn:
                user_id = await self.get_internal_user_id(conn, firebase_uid)
                if not user_id:
                    logger.warning(f"Usage tracking skipped: User {firebase_uid} not found in DB")
                    return

                await conn.execute(
                    text("""
                    INSERT INTO usage_logs (user_id, feature, quantity, context)
                    VALUES (:user_id, :feature, :quantity, :context)
                    """),
                    {
                        "user_id": user_id, 
                        "feature": feature, 
                        "quantity": quantity, 
                        "context": json.dumps(context)
                    }
                )
                logger.info(f"Recorded usage for user {firebase_uid} (internal: {user_id}): {feature} (+{quantity})")
        except Exception as e:
            logger.error(f"Failed to track usage for {firebase_uid}: {e}")

    async def get_usage_for_period(
        self,
        conn, # Pass existing connection to reuse transaction/session
        user_id: UUID,
        feature: str,
        period: str = 'daily'
    ) -> int:
        """Returns total usage for the current period."""
        now = datetime.utcnow()
        if period == 'hourly':
            start_date = now.replace(minute=0, second=0, microsecond=0)
        elif period == 'daily':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'monthly':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'yearly':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'total':
             start_date = datetime(2000, 1, 1)
        else:
            raise ValueError(f"Invalid period: {period}")

        result = await conn.execute(
            text("""
            SELECT SUM(quantity) 
            FROM usage_logs 
            WHERE user_id = :user_id AND feature = :feature AND created_at >= :start_date
            """),
            {"user_id": user_id, "feature": feature, "start_date": start_date}
        )
        total = result.scalar()
        return total or 0

    async def check_limit(self, firebase_uid: str, role: str, feature: str) -> None:
        """
        Checks if the user has exceeded their limit for the given feature.
        Raises HTTPException(403) if limit exceeded.
        """
        async with get_db_connection() as conn:
            # 1. Resolve User ID
            user_id = await self.get_internal_user_id(conn, firebase_uid)
            if not user_id:
                # If checking limit, we generally expect user to exist. 
                # If they don't, it might be a sync issue or valid new user not yet in DB (though auth should handle signup).
                # We'll fail safe and allow? OR fail secure and block?
                # Fail secure: if we can't identify, we block features.
                logger.error(f"check_limit failed: User {firebase_uid} not found")
                raise HTTPException(status_code=403, detail="User account not fully established")

            # 2. Get Limits
            result = await conn.execute(
                text("SELECT period, limit_count FROM plan_limits WHERE plan_role = :role AND feature = :feature"),
                {"role": role, "feature": feature}
            )
            limits = result.fetchall()
            
            if not limits:
                # No limits defined for this role/feature -> Allowed
                return

            for limit_row in limits:
                period = limit_row[0] # Access by index or name depending on row proxy
                limit_count = limit_row[1]
                
                # 3. Get Current Usage
                current_usage = await self.get_usage_for_period(conn, user_id, feature, period)
                
                if current_usage >= limit_count:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Usage limit exceeded for {feature} on {role} plan ({period} limit: {limit_count}. Used: {current_usage})"
                    )

# Global instance
usage_tracker = UsageTracker()
