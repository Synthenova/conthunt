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
from app.services.streak_tracker import record_streak_activity_once_per_day


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
                await record_streak_activity_once_per_day(
                    conn,
                    user_id=user_id,
                    streak_type="analysis",
                    timezone=timezone,
                    source=context_source,
                )
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

    async def trigger_paid_analysis_batch(
        self,
        user_id: UUID,
        user_role: str,
        media_asset_ids: list[UUID],
        background_tasks: Optional[BackgroundTasks] = None,
        context_source: str = "api_batch",
        record_streak: bool = True,
        chat_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Batch variant of trigger_paid_analysis preserving credit/access semantics.
        """
        from app.api.v1.analysis import run_gemini_analysis_batch
        deduped_ids = list(dict.fromkeys(media_asset_ids))
        if not deduped_ids:
            return {"accepted_media_asset_ids": [], "responses": {}}

        responses: dict[str, Any] = {}
        accepted_ids: list[UUID] = []

        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            result = await conn.execute(
                text("SELECT current_period_start, timezone FROM users WHERE id = :id"),
                {"id": user_id},
            )
            row = result.fetchone()
            period_start = row[0] if row else None
            timezone = row[1] if row and row[1] else "UTC"

            accessed_result = await conn.execute(
                text(
                    """
                    SELECT media_asset_id
                    FROM user_analysis_access
                    WHERE user_id = :user_id
                      AND media_asset_id = ANY(:media_asset_ids)
                    """
                ),
                {"user_id": user_id, "media_asset_ids": deduped_ids},
            )
            already_accessed = {r[0] for r in accessed_result.fetchall()}

            for media_asset_id in deduped_ids:
                asset_key = str(media_asset_id)
                if media_asset_id not in already_accessed:
                    credit_result = await credit_tracker.check(
                        user_id=user_id,
                        role=user_role,
                        feature="video_analysis",
                        current_period_start=period_start,
                        record=True,
                        context={"media_asset_id": asset_key, "source": context_source},
                        conn=conn,
                    )
                    if not credit_result["allowed"]:
                        responses[asset_key] = {
                            "error": "Credit limit exceeded",
                            "status": "failed",
                            "media_asset_id": asset_key,
                        }
                        continue
                    await record_user_analysis_access(conn, user_id, media_asset_id)

                accepted_ids.append(media_asset_id)

            # Record one streak activity per batch request, not per asset.
            if record_streak and accepted_ids:
                await record_streak_activity_once_per_day(
                    conn,
                    user_id=user_id,
                    streak_type="analysis",
                    timezone=timezone,
                    source=context_source,
                )

            await conn.commit()

        if accepted_ids:
            batch_responses = await run_gemini_analysis_batch(
                media_asset_ids=accepted_ids,
                background_tasks=background_tasks,
                use_cloud_tasks=True,
                chat_id=chat_id,
                user_id=str(user_id),
            )
            for response in batch_responses:
                responses[str(response.media_asset_id)] = (
                    response.model_dump() if hasattr(response, "model_dump") else response.__dict__
                )

        return {
            "accepted_media_asset_ids": [str(asset_id) for asset_id in accepted_ids],
            "responses": responses,
        }


# Global instance
analysis_service = AnalysisService()
