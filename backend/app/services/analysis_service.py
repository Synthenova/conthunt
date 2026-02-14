"""Analysis service with credit enforcement."""
from uuid import UUID
from typing import Dict, Any, Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import text

from app.core import logger
from app.db.session import get_db_connection
from app.db.queries.analysis import has_user_accessed_analysis, record_user_analysis_access
from app.db import set_rls_user
from app.services.credit_tracker import credit_tracker


class AnalysisService:
    """
    Centralized service for video analysis with credit enforcement.
    """

    async def trigger_paid_analysis(
        self,
        user_id: UUID,
        user_role: str,
        media_asset_id: UUID,
        background_tasks: Optional[BackgroundTasks] = None,
        context_source: str = "api",
        record_streak: bool = True,
        chat_id: str | None = None,
    ) -> Dict[str, Any]:
        """
        Trigger a paid video analysis.
        
        All analysis goes through the unified run_gemini_analysis flow which:
        - Uses atomic claim to prevent race conditions
        - Dispatches priority download if asset is pending
        - Spawns background task for LLM processing
        
        Checks if user already accessed this analysis (free re-access).
        If not, checks credit limits and charges.
        """
        # Import here to avoid circular dependency
        from app.api.v1.analysis import run_gemini_analysis
        
        # Get user's period_start for credit tracking
        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            result = await conn.execute(
                text("SELECT current_period_start, timezone FROM users WHERE id = :id"),
                {"id": user_id}
            )
            row = result.fetchone()
            period_start = row[0] if row else None
            timezone = row[1] if row and row[1] else "UTC"
            
            # Check if already accessed (free re-view)
            already_accessed = await has_user_accessed_analysis(conn, user_id, media_asset_id)
            logger.info(f"[DEEP_SERVICE] check_access user={user_id} asset={media_asset_id} already_accessed={already_accessed}")
        
            if not already_accessed:
                # First access - check and charge credits
                credit_result = await credit_tracker.check(
                    user_id=user_id,
                    role=user_role,
                    feature="video_analysis",
                    current_period_start=period_start,
                    record=True,
                    context={"media_asset_id": str(media_asset_id), "source": context_source},
                    conn=conn,
                )
                if not credit_result["allowed"]:
                    raise HTTPException(status_code=402, detail="Credit limit exceeded")
                
                # Record access for future free re-views
                await record_user_analysis_access(conn, user_id, media_asset_id)
                
                logger.info(f"Charged credit for analysis: user={user_id}, asset={media_asset_id}")
            else:
                logger.info(f"Free re-access: user={user_id} already analyzed asset={media_asset_id}")

            if record_streak:
                from app.db.queries import streaks as streak_queries
                await streak_queries.record_activity(conn, user_id, "analysis", timezone=timezone)
            await conn.commit()
        
        # Trigger unified analysis flow (handles priority downloads, race conditions, etc.)
        logger.info(f"[{context_source}] Triggering unified analysis for {media_asset_id}")
        return await run_gemini_analysis(
            media_asset_id=media_asset_id,
            background_tasks=background_tasks,
            use_cloud_tasks=True,
            chat_id=chat_id,
            user_id=str(user_id),
        )


# Global instance
analysis_service = AnalysisService()
