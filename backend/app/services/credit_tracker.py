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

    def _get_credit_period_start(self, subscription_start: datetime | None) -> datetime:
        """
        Get the start of the current MONTHLY credit period.
        
        Credits reset monthly based on subscription anniversary date, NOT billing cycle.
        
        Example:
          - User subscribed on Jan 15
          - Today is Mar 20
          - Current credit period: Mar 15 to Apr 15
          - Returns: Mar 15
        
        This ensures both monthly and yearly subscribers get monthly credit resets.
        """
        now = datetime.utcnow()
        
        if not subscription_start:
            # Fallback: use 1st of current month
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get the anniversary day (capped at 28 to handle Feb edge cases)
        anniversary_day = min(subscription_start.day, 28)
        
        # Calculate which monthly period we're in
        # Start with this month's anniversary
        this_month_anniversary = now.replace(
            day=anniversary_day, 
            hour=0, minute=0, second=0, microsecond=0
        )
        
        if now >= this_month_anniversary:
            # We're past this month's anniversary, so current period started this month
            return this_month_anniversary
        else:
            # We haven't hit this month's anniversary yet, period started last month
            # Go to previous month
            if now.month == 1:
                return now.replace(
                    year=now.year - 1, 
                    month=12, 
                    day=anniversary_day,
                    hour=0, minute=0, second=0, microsecond=0
                )
            else:
                return now.replace(
                    month=now.month - 1, 
                    day=anniversary_day,
                    hour=0, minute=0, second=0, microsecond=0
                )

    def _get_period_start(self, current_period_start: datetime | None) -> datetime:
        """
        DEPRECATED: Use _get_credit_period_start for monthly credits.
        Kept for backward compatibility.
        """
        return self._get_credit_period_start(current_period_start)


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

    # =========================================================================
    # SUBSCRIPTION LIFECYCLE CREDIT METHODS
    # =========================================================================

    async def get_plan_credits(self, conn, role: str) -> int:
        """Get total credits for a plan role."""
        result = await conn.execute(
            text("SELECT total_credits FROM plan_credits WHERE plan_role = :role"),
            {"role": role}
        )
        row = result.fetchone()
        return row[0] if row else 0

    async def grant_cycle_credits(
        self,
        user_id: UUID,
        role: str,
        period_start: datetime,
        reason: str = "renewal",
    ) -> int:
        """
        Grant full cycle credits for a new billing period.
        
        This is a no-op in the "usage since date" model - credits are
        implicitly reset when period_start changes. This method exists
        for explicit logging/auditing.
        
        Returns the total credits available for the new cycle.
        """
        async with get_db_connection() as conn:
            total_credits = await self.get_plan_credits(conn, role)
            
            # Log the credit grant event for auditing
            await conn.execute(
                text("""
                INSERT INTO usage_logs (user_id, feature, quantity, context)
                VALUES (:user_id, :feature, :quantity, :context)
                """),
                {
                    "user_id": user_id,
                    "feature": "credit_grant",
                    "quantity": 0,  # No actual deduction
                    "context": json.dumps({
                        "type": reason,
                        "role": role,
                        "credits_granted": total_credits,
                        "period_start": period_start.isoformat() if period_start else None,
                    })
                }
            )
            
            logger.info(f"Credits: {user_id} | {reason} | +{total_credits} for {role}")
            return total_credits

    async def grant_upgrade_topup(
        self,
        user_id: UUID,
        old_role: str,
        new_role: str,
    ) -> int:
        """
        Grant top-up credits on upgrade (Option A).
        
        Top-up = new_plan_credits - old_plan_credits
        
        If the user had used some credits on the old plan, they keep that
        usage but gain the difference in total allowance.
        
        Returns the top-up amount granted.
        """
        async with get_db_connection() as conn:
            old_credits = await self.get_plan_credits(conn, old_role)
            new_credits = await self.get_plan_credits(conn, new_role)
            
            topup = max(0, new_credits - old_credits)
            
            if topup > 0:
                # Log the top-up for auditing
                await conn.execute(
                    text("""
                    INSERT INTO usage_logs (user_id, feature, quantity, context)
                    VALUES (:user_id, :feature, :quantity, :context)
                    """),
                    {
                        "user_id": user_id,
                        "feature": "credit_grant",
                        "quantity": 0,  # No actual deduction
                        "context": json.dumps({
                            "type": "upgrade_topup",
                            "old_role": old_role,
                            "new_role": new_role,
                            "old_credits": old_credits,
                            "new_credits": new_credits,
                            "topup": topup,
                        })
                    }
                )
                
                logger.info(f"Credits: {user_id} | upgrade | +{topup} ({old_role} → {new_role})")
            
            return topup

    async def on_subscription_sync(
        self,
        user_id: UUID,
        old_subscription: dict | None,
        new_subscription: dict,
    ) -> dict:
        """
        Handle credit operations after subscription sync.
        
        Called by webhook handler after upserting user_subscriptions.
        Detects and handles:
        - Renewal: period_start changed → grant full cycle credits
        - Upgrade: product_id changed, same period → grant top-up
        
        Returns dict with credit_event and credits_granted.
        """
        result = {"credit_event": None, "credits_granted": 0}
        
        new_period_start = new_subscription.get("current_period_start")
        new_product_id = new_subscription.get("product_id")
        new_status = new_subscription.get("status")
        
        # Only process active subscriptions
        if new_status not in ("active", "trialing"):
            return result
        
        # Get role for new product
        from app.db.queries.billing import get_role_for_product
        async with get_db_connection() as conn:
            new_role = await get_role_for_product(conn, new_product_id)
        
        if not new_role:
            return result
        
        if old_subscription:
            old_period_start = old_subscription.get("current_period_start")
            old_product_id = old_subscription.get("product_id")
            
            # Get old role
            if old_product_id:
                async with get_db_connection() as conn:
                    old_role = await get_role_for_product(conn, old_product_id)
            else:
                old_role = None
            
            # RENEWAL: period_start changed
            if old_period_start and new_period_start and old_period_start != new_period_start:
                credits = await self.grant_cycle_credits(
                    user_id=user_id,
                    role=new_role,
                    period_start=new_period_start,
                    reason="renewal",
                )
                result["credit_event"] = "renewal"
                result["credits_granted"] = credits
            
            # UPGRADE: product changed within same period
            elif old_product_id and new_product_id and old_product_id != new_product_id:
                if old_period_start == new_period_start and old_role:
                    topup = await self.grant_upgrade_topup(
                        user_id=user_id,
                        old_role=old_role,
                        new_role=new_role,
                    )
                    result["credit_event"] = "upgrade"
                    result["credits_granted"] = topup
        else:
            # NEW SUBSCRIPTION
            credits = await self.grant_cycle_credits(
                user_id=user_id,
                role=new_role,
                period_start=new_period_start,
                reason="new_subscription",
            )
            result["credit_event"] = "new_subscription"
            result["credits_granted"] = credits
        
        return result


# Global instance
credit_tracker = CreditTracker()

