"""Credit-based usage tracking with monthly credit period resets."""
import json
from uuid import UUID
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from app.db.session import get_db_connection
from app.db import set_rls_user
from app.core import logger, get_settings


# Feature credit costs (hardcoded)
FEATURE_CREDITS = {
    "search_query": 1,
    "video_analysis": 2,
    "index_video": 5,
}

# Role to monthly credits mapping (matches Dodo product metadata)
ROLE_CREDITS = {
    "free": 1000 if get_settings().APP_ENV == "local" else 60,
    "creator": 1050,
    "pro_research": 3300,
}

# Credit period duration (30 days regardless of billing cycle)
CREDIT_PERIOD_DAYS = 30


class CreditTracker:
    """
    Usage tracking with monthly credit periods.
    Credits reset every 30 days from the subscription start date.
    Works for both monthly and yearly billing cycles.
    """

    async def _get_credit_period_start(self, conn, user_id: UUID) -> Optional[datetime]:
        """Get user's current credit period start from database."""
        result = await conn.execute(
            text("SELECT credit_period_start FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        row = result.fetchone()
        return row[0] if row and row[0] else None

    async def _get_reward_balance(
        self,
        conn,
        user_id: UUID,
        reward_feature: str | None,
    ) -> int:
        if reward_feature is None:
            result = await conn.execute(
                text("""
                SELECT balance
                FROM reward_balances
                WHERE user_id = :user_id AND reward_feature IS NULL
                """),
                {"user_id": user_id}
            )
        else:
            result = await conn.execute(
                text("""
                SELECT balance
                FROM reward_balances
                WHERE user_id = :user_id AND reward_feature = :reward_feature
                """),
                {"user_id": user_id, "reward_feature": reward_feature}
            )
        row = result.fetchone()
        return row[0] if row and row[0] is not None else 0

    async def _get_reward_balances(self, conn, user_id: UUID) -> dict[str, int]:
        result = await conn.execute(
            text("""
            SELECT reward_feature, balance
            FROM reward_balances
            WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        )
        balances = {}
        for row in result.fetchall():
            key = "credits" if row[0] is None else row[0]
            balances[key] = row[1]
        return balances

    async def _decrement_reward_balance(
        self,
        conn,
        user_id: UUID,
            reward_feature: str | None,
            amount: int,
    ) -> None:
        if amount <= 0:
            return
        if reward_feature is None:
            await conn.execute(
                text("""
                UPDATE reward_balances
                SET balance = GREATEST(balance - :amount, 0),
                    updated_at = NOW()
                WHERE user_id = :user_id AND reward_feature IS NULL
                """),
                {"user_id": user_id, "amount": amount}
            )
        else:
            await conn.execute(
                text("""
                UPDATE reward_balances
                SET balance = GREATEST(balance - :amount, 0),
                    updated_at = NOW()
                WHERE user_id = :user_id AND reward_feature = :reward_feature
                """),
                {"user_id": user_id, "reward_feature": reward_feature, "amount": amount}
            )

    async def _advance_credit_period_if_needed(self, conn, user_id: UUID, current_period: datetime) -> datetime:
        """
        Check if 30 days have passed since credit_period_start.
        If so, advance to next period (keeping alignment with original start date).
        Returns the effective period start for credit calculations.
        """
        now = datetime.utcnow()
        # Strip timezone info for comparison (DB may return tz-aware)
        if current_period.tzinfo is not None:
            current_period = current_period.replace(tzinfo=None)
        period_end = current_period + timedelta(days=CREDIT_PERIOD_DAYS)
        
        if now >= period_end:
            # Calculate how many periods have passed
            days_since_start = (now - current_period).days
            periods_passed = days_since_start // CREDIT_PERIOD_DAYS
            
            # Advance to current period (maintains alignment with original date)
            new_period_start = current_period + timedelta(days=periods_passed * CREDIT_PERIOD_DAYS)
            
            # Update in database
            await conn.execute(
                text("""
                UPDATE users SET credit_period_start = :new_period
                WHERE id = :user_id
                """),
                {"user_id": user_id, "new_period": new_period_start}
            )
            
            logger.info(f"Advanced credit period for user {user_id}: {current_period} -> {new_period_start}")
            return new_period_start
        
        return current_period

    async def record_usage(
        self,
        user_id: UUID,
        feature: str,
        context: Optional[dict] = None,
        conn: Optional[AsyncConnection] = None,
    ) -> None:
        """
        Record usage. Credits consumed = FEATURE_CREDITS[feature].
        Fail-safe: logs errors instead of raising.
        """
        credit_cost = FEATURE_CREDITS.get(feature, 1)
        context = context or {}
        context["credit_cost"] = credit_cost
        
        try:
            if conn is None:
                async with get_db_connection() as local_conn:
                    await set_rls_user(local_conn, user_id)
                    await local_conn.execute(
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
            else:
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
        context: Optional[dict] = None,
        conn: Optional[AsyncConnection] = None,
    ) -> dict:
        """
        Check and optionally record usage against credit limits.
        """
        credit_cost = FEATURE_CREDITS.get(feature, 1)
        total_credits = ROLE_CREDITS.get(role, 50)

        async def _ensure_period_start(active_conn: AsyncConnection) -> datetime:
            period_start = await self._get_credit_period_start(active_conn, user_id)
            if not period_start:
                period_start = current_period_start or datetime.utcnow()
            else:
                period_start = await self._advance_credit_period_if_needed(
                    active_conn, user_id, period_start
                )
            return period_start

        async def _check_with_conn(active_conn: AsyncConnection) -> dict:
            settings = get_settings()
            await set_rls_user(active_conn, user_id)
            period_start = await _ensure_period_start(active_conn)

            limit_result = await active_conn.execute(
                text("""
                SELECT limit_count
                FROM usage_limits
                WHERE plan_role = :role AND feature = :feature AND period = 'monthly'
                """),
                {"role": role, "feature": feature}
            )
            limit_row = limit_result.fetchone()
            limit_count = limit_row[0] if limit_row else None

            used_result = await active_conn.execute(
                text("""
                SELECT COUNT(*)
                FROM usage_logs
                WHERE user_id = :user_id
                  AND feature = :feature
                  AND created_at >= :period_start
                """),
                {"user_id": user_id, "feature": feature, "period_start": period_start}
            )
            used = used_result.scalar() or 0

            bonus_feature = await self._get_reward_balance(active_conn, user_id, feature)
            bonus_credits = await self._get_reward_balance(active_conn, user_id, None)
            credits_used = await self.get_credits_used(active_conn, user_id, period_start)
            credit_remaining = max(0, total_credits + bonus_credits - credits_used)
            if limit_count is None:
                remaining_before = None
                allowed = credit_remaining >= credit_cost
            else:
                remaining_before = max(0, limit_count + bonus_feature - used)
                allowed = credit_remaining >= credit_cost and remaining_before >= 1

            if allowed and record:
                await self.record_usage(user_id, feature, context, conn=active_conn)
                if limit_count is not None and used >= limit_count:
                    await self._decrement_reward_balance(active_conn, user_id, feature, 1)
                if credits_used >= total_credits:
                    await self._decrement_reward_balance(active_conn, user_id, None, credit_cost)

            response = {
                "allowed": allowed,
                "credits_remaining": max(
                    0, credit_remaining - (credit_cost if allowed and record else 0)
                ),
                "feature_uses_remaining": None if remaining_before is None else max(
                    0, remaining_before - (1 if allowed and record else 0)
                ),
            }

            return response

        if conn is None:
            async with get_db_connection() as local_conn:
                return await _check_with_conn(local_conn)

        return await _check_with_conn(conn)

    async def get_usage_summary(
        self,
        user_id: UUID,
        role: str,
        current_period_start: datetime | None = None
    ) -> dict:
        """
        Get usage summary with actual credit limits based on role.
        Automatically advances credit period if 30 days have passed.
        """
        # Get credit limit based on role
        total_credits = ROLE_CREDITS.get(role, 50)
        
        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            # Get credit period start from DB
            period_start = await self._get_credit_period_start(conn, user_id)
            
            # If no credit period set, use provided or default to now
            if not period_start:
                period_start = current_period_start or datetime.utcnow()
            else:
                # Check if we need to advance the period (30 days passed)
                period_start = await self._advance_credit_period_if_needed(conn, user_id, period_start)
            
            # Load monthly usage limits per feature for this role.
            limits_result = await conn.execute(
                text("""
                SELECT feature, limit_count
                FROM usage_limits
                WHERE plan_role = :role AND period = 'monthly'
                """),
                {"role": role}
            )
            usage_limits = {row[0]: row[1] for row in limits_result.fetchall()}

            # Get usage per feature within current credit period
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
                    "cap": usage_limits.get(feature),
                    "remaining": None,
                }
                if credits > 0:
                    total_credits_used += credits

            # Add any limited features with zero usage.
            for feature, cap in usage_limits.items():
                if feature in features:
                    features[feature]["remaining"] = max(0, cap - features[feature]["uses"])
                    continue
                features[feature] = {
                    "uses": 0,
                    "credits_spent": 0,
                    "cap": cap,
                    "remaining": cap,
                }
            
            # Calculate next reset date
            next_reset = period_start + timedelta(days=CREDIT_PERIOD_DAYS)
            
            reward_balances = await self._get_reward_balances(conn, user_id)
            bonus_credits = reward_balances.get("credits", 0)
            bonus_searches = reward_balances.get("search_query", 0)

            return {
                "credits": {
                    "total": total_credits,
                    "used": total_credits_used,
                    "bonus": bonus_credits,
                    "remaining": max(0, total_credits + bonus_credits - total_credits_used),
                },
                "reward_balances": reward_balances,
                "features": features,
                "period_start": period_start.isoformat() + "Z",
                "next_reset": next_reset.isoformat() + "Z",
            }


# Global instance
credit_tracker = CreditTracker()
