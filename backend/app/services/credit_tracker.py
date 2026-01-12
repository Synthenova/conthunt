"""Credit-based usage tracking (Counting only)."""
import json
from uuid import UUID
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from app.db.session import get_db_connection
from app.db import set_rls_user
from app.core import logger


# Feature credit costs (hardcoded)
FEATURE_CREDITS = {
    "search_query": 1,
    "video_analysis": 2,
    "index_video": 5,
}


class CreditTracker:
    """
    Usage tracking only. No limits enforced.
    """

    async def record_usage(
        self,
        user_id: UUID,
        feature: str,
        context: Optional[dict] = None
    ) -> None:
        """
        Record usage. Credits consumed = FEATURE_CREDITS[feature].
        Fail-safe: logs errors instead of raising.
        """
        credit_cost = FEATURE_CREDITS.get(feature, 1)
        context = context or {}
        context["credit_cost"] = credit_cost
        
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
                        "quantity": credit_cost,
                        "context": json.dumps(context)
                    }
                )
                logger.info(f"Usage: {user_id} | {feature} | -{credit_cost} credits")
        except Exception as e:
            logger.error(f"Failed to record usage for {user_id}: {e}")

    async def get_credits_used(
        self,
        conn,
        user_id: UUID,
        period_start: datetime
    ) -> int:
        """Get total credits used since period_start."""
        result = await conn.execute(
            text("""
            SELECT COALESCE(SUM(quantity), 0)
            FROM usage_logs
            WHERE user_id = :user_id AND created_at >= :period_start
            """),
            {"user_id": user_id, "period_start": period_start}
        )
        return result.scalar() or 0

    async def get_feature_uses(
        self,
        conn,
        user_id: UUID,
        feature: str,
        period_start: datetime
    ) -> int:
        """Get number of times a feature was used (count, not credits)."""
        result = await conn.execute(
            text("""
            SELECT COUNT(*)
            FROM usage_logs
            WHERE user_id = :user_id 
              AND feature = :feature 
              AND created_at >= :period_start
            """),
            {"user_id": user_id, "feature": feature, "period_start": period_start}
        )
        return result.scalar() or 0

    async def check(
        self,
        user_id: UUID,
        role: str,
        feature: str,
        current_period_start: datetime | None = None,
        record: bool = True,
        context: Optional[dict] = None
    ) -> dict:
        """
        Check simply records usage if requested. Always returns allowed=True.
        """
        credit_cost = FEATURE_CREDITS.get(feature, 1)
        
        # Record usage if requested
        if record:
            await self.record_usage(user_id, feature, context)
        
        # We just return simplified info as we don't track limits anymore
        return {
            "allowed": True,
            "credits_remaining": 999999, # Infinite
            "feature_uses_remaining": None,
        }

    async def get_usage_summary(
        self,
        user_id: UUID,
        role: str,
        current_period_start: datetime | None = None
    ) -> dict:
        """
        Get usage summary (just what has been used).
        """
        # Fallback period start if none provided
        period_start = current_period_start or datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        async with get_db_connection() as conn:
            # Get usage per feature
            result = await conn.execute(
                text("""
                SELECT feature, COUNT(*) as uses, COALESCE(SUM(quantity), 0) as credits
                FROM usage_logs
                WHERE user_id = :user_id AND created_at >= :period_start
                GROUP BY feature
                """),
                {"user_id": user_id, "period_start": period_start}
            )
            
            features = {}
            total_credits_used = 0
            for row in result.fetchall():
                feature, uses, credits = row[0], row[1], row[2]
                features[feature] = {
                    "uses": uses,
                    "credits_spent": credits,
                    "cap": None,
                    "remaining": None,
                }
                total_credits_used += credits
            
            return {
                "credits": {
                    "total": 999999,
                    "used": total_credits_used,
                    "remaining": 999999 - total_credits_used,
                },
                "features": features,
                "period_start": period_start.isoformat() + "Z",
            }


# Global instance
credit_tracker = CreditTracker()
