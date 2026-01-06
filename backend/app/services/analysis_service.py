from uuid import UUID
from typing import Dict, Any, Optional

from fastapi import BackgroundTasks

from app.core import logger
from app.db.session import get_db_connection
from app.services.usage_tracker import usage_tracker
from app.api.v1.analysis import run_gemini_analysis
from app.agent.analysis_inline import run_inline_video_analysis

class AnalysisService:
    """
    Centralized service for video analysis with credit enforcement.
    Ensures all analysis paths (API, Agent, Board Insights) go through
    the same credit consumption logic.
    """

    async def trigger_paid_analysis(
        self,
        user_id: UUID,
        user_role: str,
        media_asset_id: UUID,
        wait: bool = False,
        background_tasks: Optional[BackgroundTasks] = None,
        context_source: str = "api",
    ) -> Dict[str, Any]:
        """
        Trigger a paid video analysis.
        
        Args:
            user_id: The internal DB UUID of the requesting user.
            user_role: The user's role (for limit checking).
            media_asset_id: The video media asset to analyze.
            wait: If True, runs inline and waits for result (for Agent).
                  If False, spawns background task and returns immediately (for API).
            background_tasks: Optional FastAPI BackgroundTasks (for API/async).
            context_source: Source identifier for usage tracking logs.
            
        Returns:
            Dict containing analysis response (status, analysis, etc.)
            
        Raises:
            HTTPException (403): If usage limit exceeded.
        """
        # 1. Check Limits & Charge Credit (using UUID directly)
        await usage_tracker.check_and_record_analysis_access(
            user_id=user_id,
            user_role=user_role,
            media_asset_id=media_asset_id,
            context={"source": context_source}
        )
        
        # 2. Trigger Analysis (Cached check is handled inside these functions too)
        if wait:
            # Inline execution (slower, but returns result immediately)
            # Used by Agent Tools
            logger.info(f"[{context_source}] Running inline analysis for {media_asset_id}")
            return await run_inline_video_analysis(media_asset_id)
        else:
            # Background execution (returns 'processing' status)
            # Used by API and Board Insights
            logger.info(f"[{context_source}] Spawning background analysis for {media_asset_id}")
            return await run_gemini_analysis(
                media_asset_id=media_asset_id,
                background_tasks=background_tasks,
                use_cloud_tasks=True
            )

# Global instance
analysis_service = AnalysisService()
