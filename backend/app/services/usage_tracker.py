import json
from uuid import UUID
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from app.db.session import get_db_connection
from app.core import logger

from app.db import set_rls_user

class UsageTracker:
    """
    Usage tracking service. 
    All methods accept user_id (UUID) directly - no firebase_uid lookups.
    """

    async def record_usage(
        self,
        user_id: UUID,
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
                await set_rls_user(conn, user_id)

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
                logger.info(f"Recorded usage for user {user_id}: {feature} (+{quantity})")
        except Exception as e:
            logger.error(f"Failed to track usage for {user_id}: {e}")

    async def get_usage_for_period(
        self,
        conn,
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

    async def check_limit(self, user_id: UUID, role: str, feature: str) -> None:
        """
        Checks if the user has exceeded their limit for the given feature.
        Raises HTTPException(403) if limit exceeded.
        
        Args:
            user_id: The internal DB UUID of the user
            role: The user's role (e.g., 'free', 'pro')
            feature: The feature to check limits for (e.g., 'gemini_analysis')
        """
        logger.info(f"Checking limit for {user_id} (role={role}, feature={feature})")

        async with get_db_connection() as conn:
            result = await conn.execute(
                text("SELECT period, limit_count FROM plan_limits WHERE plan_role = :role AND feature = :feature"),
                {"role": role, "feature": feature}
            )
            limits = result.fetchall()
            
            if not limits:
                logger.info(f"No limits defined for {role} / {feature}. Allowing.")
                return

            for limit_row in limits:
                period = limit_row[0]
                limit_count = limit_row[1]
                
                current_usage = await self.get_usage_for_period(conn, user_id, feature, period)
                
                logger.info(
                    f"Usage Check: {user_id} ({role}) - {feature} "
                    f"[{period}]: {current_usage}/{limit_count}"
                )
                
                if current_usage >= limit_count:
                    logger.warning(
                        f"Limit exceeded for {user_id} ({role}): "
                        f"{feature} usage={current_usage}, limit={limit_count}, period={period}"
                    )
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Usage limit exceeded for {feature} on {role} plan ({period} limit: {limit_count}. Used: {current_usage})"
                    )

    async def get_usage_summary(self, user_id: UUID, role: str) -> list:
        """Returns a list of usage vs limits for all features for this role."""
        async with get_db_connection() as conn:
            result = await conn.execute(
                text("SELECT feature, period, limit_count FROM plan_limits WHERE plan_role = :role"),
                {"role": role}
            )
            limits = result.fetchall()
            
            summary = []
            for limit_row in limits:
                feature = limit_row[0]
                period = limit_row[1]
                limit_count = limit_row[2]
                
                current_usage = await self.get_usage_for_period(conn, user_id, feature, period)
                summary.append({
                    "feature": feature,
                    "period": period,
                    "limit": limit_count,
                    "used": current_usage
                })
            return summary

    async def check_and_record_analysis_access(
        self,
        user_id: UUID,
        user_role: str,
        media_asset_id: UUID,
        context: Optional[dict] = None,
    ) -> bool:
        """
        Check if user has accessed this analysis before. If not, check limits,
        record access, and record usage.
        
        Args:
            user_id: The internal DB UUID of the user
            user_role: User's role for limit checking
            media_asset_id: The media asset being analyzed
            context: Optional context for usage logging
        
        Returns True if this is first access (credit charged), False if already accessed.
        Raises HTTPException(403) if limit exceeded.
        """
        from app.db.queries.analysis import has_user_accessed_analysis, record_user_analysis_access
        
        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            
            # Check if user already accessed this analysis
            already_accessed = await has_user_accessed_analysis(conn, user_id, media_asset_id)
            if already_accessed:
                logger.info(f"User {user_id} already accessed analysis for {media_asset_id}, no credit charged")
                return False
        
        # Check limits (opens its own connection)
        await self.check_limit(user_id, user_role, "gemini_analysis")
        
        # Record access
        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            await record_user_analysis_access(conn, user_id, media_asset_id)
            await conn.commit()
        
        # Record usage
        await self.record_usage(
            user_id=user_id,
            feature="gemini_analysis",
            quantity=1,
            context={"media_asset_id": str(media_asset_id), **(context or {})}
        )
        
        logger.info(f"First access for user {user_id} to analysis {media_asset_id}, credit charged")
        return True

# Global instance
usage_tracker = UsageTracker()
