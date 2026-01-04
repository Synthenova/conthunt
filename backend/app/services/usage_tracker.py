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

                # Set RLS context for the background task
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
        # DEBUG LOG: Function Entry
        logger.info(f"Checking limit for {firebase_uid} (role={role}, feature={feature})")

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
                logger.info(f"No limits defined for {role} / {feature}. Allowing.")
                return

            for limit_row in limits:
                period = limit_row[0] # Access by index or name depending on row proxy
                limit_count = limit_row[1]
                
                # 3. Get Current Usage
                current_usage = await self.get_usage_for_period(conn, user_id, feature, period)
                
                logger.info(
                    f"Usage Check: {firebase_uid} ({role}) - {feature} "
                    f"[{period}]: {current_usage}/{limit_count}"
                )
                
                if current_usage >= limit_count:
                    logger.warning(
                        f"Limit exceeded for {firebase_uid} ({role}): "
                        f"{feature} usage={current_usage}, limit={limit_count}, period={period}"
                    )
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Usage limit exceeded for {feature} on {role} plan ({period} limit: {limit_count}. Used: {current_usage})"
                    )

    async def get_usage_summary(self, firebase_uid: str, role: str) -> list:
        """Returns a list of usage vs limits for all features for this role."""
        async with get_db_connection() as conn:
            user_id = await self.get_internal_user_id(conn, firebase_uid)
            if not user_id:
                return []

            result = await conn.execute(
                text("SELECT feature, period, limit_count FROM plan_limits WHERE plan_role = :role"),
                {"role": role}
            )
            # Use fetchall() and access by index for compatibility
            limits = result.fetchall()
            
            summary = []
            for limit_row in limits:
                feature = limit_row[0] # feature
                period = limit_row[1]  # period
                limit_count = limit_row[2] # limit_count
                
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
        firebase_uid: str,
        user_role: str,
        media_asset_id: UUID,
        context: Optional[dict] = None,
    ) -> bool:
        """
        Check if user has accessed this analysis before. If not, check limits,
        record access, and record usage.
        
        Returns True if this is first access (credit charged), False if already accessed.
        Raises HTTPException(403) if limit exceeded.
        """
        from app.db.queries.analysis import has_user_accessed_analysis, record_user_analysis_access
        
        async with get_db_connection() as conn:
            user_id = await self.get_internal_user_id(conn, firebase_uid)
            if not user_id:
                logger.error(f"check_and_record_analysis_access failed: User {firebase_uid} not found")
                raise HTTPException(status_code=403, detail="User account not fully established")
            
            # Debug: Check current role and RLS setting
            role_result = await conn.execute(text("SELECT current_user, current_setting('app.user_id', true)"))
            role_row = role_result.fetchone()
            logger.info(f"[DEBUG] Before set_rls_user - DB role: {role_row[0]}, app.user_id: {role_row[1]}")
            
            # Set RLS context for all operations in this connection
            await set_rls_user(conn, user_id)
            
            # Debug: Verify RLS was set
            rls_result = await conn.execute(text("SELECT current_setting('app.user_id', true)"))
            rls_row = rls_result.fetchone()
            logger.info(f"[DEBUG] After set_rls_user - app.user_id: {rls_row[0]}, expected: {user_id}")
            
            # Check if user already accessed this analysis
            already_accessed = await has_user_accessed_analysis(conn, user_id, media_asset_id)
            if already_accessed:
                logger.info(f"User {firebase_uid} already accessed analysis for {media_asset_id}, no credit charged")
                return False
            
            # Check limits before allowing first access
            # Note: check_limit opens its own connection, which is fine
            await self.check_limit(firebase_uid, user_role, "gemini_analysis")
            
            # Record access (RLS already set on this connection)
            logger.info(f"[DEBUG] About to insert - user_id: {user_id}, media_asset_id: {media_asset_id}")
            await record_user_analysis_access(conn, user_id, media_asset_id)
            await conn.commit()
        
        # Record usage (opens its own connection with RLS)
        await self.record_usage(
            firebase_uid=firebase_uid,
            feature="gemini_analysis",
            quantity=1,
            context={"media_asset_id": str(media_asset_id), **(context or {})}
        )
        
        logger.info(f"First access for user {firebase_uid} to analysis {media_asset_id}, credit charged")
        return True

# Global instance
usage_tracker = UsageTracker()
