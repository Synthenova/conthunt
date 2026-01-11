"""Credit-based usage tracking with billing cycle awareness."""
import json
from uuid import UUID
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from app.db.session import get_db_connection
from app.db import set_rls_user
from app.core import logger


# Feature credit costs (hardcoded for speed, MIRRORS DB)
FEATURE_CREDITS = {
    "search_query": 1,
    "video_analysis": 2,
    "index_video": 5,
}


class CreditTracker:
    """
    Credit-based usage tracking.
    
    Two checks per feature:
    1. Feature cap: Has user exceeded the per-feature limit? (e.g., 50 searches)
    2. Credit pool: Does user have enough credits remaining?
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

    def _get_period_start(self, current_period_start: datetime | None) -> datetime:
        """Get billing period start, fallback to 1st of month if not set."""
        if current_period_start:
            return current_period_start
        
        now = datetime.utcnow()
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

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
        Check limits and optionally record usage.
        
        Args:
            user_id: Internal DB UUID
            role: User's plan role
            feature: Feature being used
            current_period_start: Billing period start (falls back to 1st of month)
            record: If True, record usage after successful check
            context: Optional context for usage log
        
        Returns: {"allowed": bool, "credits_remaining": int, "feature_uses_remaining": int | None}
        Raises: HTTPException(403) if limit exceeded
        """
        credit_cost = FEATURE_CREDITS.get(feature, 1)
        period_start = self._get_period_start(current_period_start)
        
        async with get_db_connection() as conn:
            # 1. Get plan's total credits
            result = await conn.execute(
                text("SELECT total_credits FROM plan_credits WHERE plan_role = :role"),
                {"role": role}
            )
            row = result.fetchone()
            total_credits = row[0] if row else 0
            
            # 2. Get credits used this period
            credits_used = await self.get_credits_used(conn, user_id, period_start)
            credits_remaining = total_credits - credits_used
            
            # 3. Check credit pool
            if credits_remaining < credit_cost:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "credits_exhausted",
                        "message": f"Not enough credits. Need {credit_cost}, have {credits_remaining}.",
                        "credits_remaining": credits_remaining,
                        "credits_needed": credit_cost,
                    }
                )
            
            # 4. Check feature cap (if exists)
            result = await conn.execute(
                text("""
                SELECT max_uses FROM feature_caps 
                WHERE plan_role = :role AND feature = :feature
                """),
                {"role": role, "feature": feature}
            )
            cap_row = result.fetchone()
            
            feature_uses_remaining = None
            if cap_row:
                max_uses = cap_row[0]
                current_uses = await self.get_feature_uses(conn, user_id, feature, period_start)
                feature_uses_remaining = max_uses - current_uses
                
                if current_uses >= max_uses:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "feature_cap_exceeded",
                            "message": f"You've reached your {feature} limit ({max_uses} per billing period).",
                            "feature": feature,
                            "max_uses": max_uses,
                            "current_uses": current_uses,
                        }
                    )
        
        # 5. Record usage if requested
        if record:
            await self.record_usage(user_id, feature, context)
            credits_remaining -= credit_cost
            if feature_uses_remaining is not None:
                feature_uses_remaining -= 1
        
        return {
            "allowed": True,
            "credits_remaining": credits_remaining,
            "feature_uses_remaining": feature_uses_remaining,
        }

    async def get_usage_summary(
        self,
        user_id: UUID,
        role: str,
        current_period_start: datetime | None = None
    ) -> dict:
        """
        Get complete usage summary for user.
        
        Returns:
        {
            "credits": {"total": 1000, "used": 150, "remaining": 850},
            "features": {
                "search_query": {"uses": 45, "credits_spent": 45, "cap": 50, "remaining": 5},
                ...
            },
            "period_start": "2026-01-15T00:00:00Z"
        }
        """
        period_start = self._get_period_start(current_period_start)
        
        async with get_db_connection() as conn:
            # Get total credits for plan
            result = await conn.execute(
                text("SELECT total_credits FROM plan_credits WHERE plan_role = :role"),
                {"role": role}
            )
            row = result.fetchone()
            total_credits = row[0] if row else 0
            
            # Get credits used
            credits_used = await self.get_credits_used(conn, user_id, period_start)
            
            # Get feature caps for this role
            result = await conn.execute(
                text("SELECT feature, max_uses FROM feature_caps WHERE plan_role = :role"),
                {"role": role}
            )
            caps = {row[0]: row[1] for row in result.fetchall()}
            
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
            for row in result.fetchall():
                feature, uses, credits = row[0], row[1], row[2]
                cap = caps.get(feature)
                features[feature] = {
                    "uses": uses,
                    "credits_spent": credits,
                    "cap": cap,
                    "remaining": cap - uses if cap else None,
                }
            
            # Add features with caps that haven't been used yet
            for feature, cap in caps.items():
                if feature not in features:
                    features[feature] = {
                        "uses": 0,
                        "credits_spent": 0,
                        "cap": cap,
                        "remaining": cap,
                    }
            
            return {
                "credits": {
                    "total": total_credits,
                    "used": credits_used,
                    "remaining": total_credits - credits_used,
                },
                "features": features,
                "period_start": period_start.isoformat() + "Z",
            }


# Global instance
credit_tracker = CreditTracker()
