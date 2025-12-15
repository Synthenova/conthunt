"""TwelveLabs video analysis API endpoints."""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.auth.firebase import get_current_user
from app.core.settings import get_settings
from app.db.session import get_db_connection
from app.db import queries
from app.schemas.twelvelabs import VideoAnalysisResponse, VideoAnalysisResult
from app.services.twelvelabs_processing import process_video_analysis

logger = logging.getLogger(__name__)
router = APIRouter(tags=["video-analysis"])


@router.post(
    "/video-analysis/{content_item_id}",
    response_model=VideoAnalysisResponse,
    summary="Analyze a video using TwelveLabs AI",
    description="""
    Analyze a video and extract structured insights including:
    - Hook (attention-grabbing opening)
    - Call to action
    - On-screen texts
    - Key topics
    - Summary
    - Suggested hashtags
    
    Results are cached globally. First request for a video triggers upload/indexing
    which may take 1-3 minutes. Subsequent requests return cached results instantly.
    """,
)

async def analyze_video(
    content_item_id: UUID,
    background_tasks: BackgroundTasks,
    _user: dict = Depends(get_current_user),
):
    """
    Trigger or retrieve video analysis for a content item.
    """
    settings = get_settings()
    
    if not settings.TWELVELABS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="TwelveLabs API is not configured"
        )
    
    async with get_db_connection() as conn:
        # 1. Check for cached analysis
        existing = await queries.get_video_analysis_by_content_item(
            conn, content_item_id
        )
        if existing:
            return VideoAnalysisResponse(
                id=existing["id"],
                content_item_id=existing["content_item_id"],
                status="completed",
                analysis=VideoAnalysisResult(**existing["analysis_result"]),
                created_at=existing["created_at"],
                cached=True,
            )
        
        # 2. Check current status of asset
        tl_asset = await queries.get_twelvelabs_asset_by_content_item(
            conn, content_item_id
        )
        
        status = "processing"
        if tl_asset:
            if tl_asset["error"]:
                # If it failed previously, we'll retry, but for now report status
                # Or maybe we just restart it below
                pass
            elif tl_asset["index_status"] == "ready":
                # Ready but no analysis? Analysis must be pending or failed.
                pass
        
        # 3. Trigger background processing
        # We trigger it if analysis doesn't exist. The task handles idempotency.
        background_tasks.add_task(process_video_analysis, content_item_id)
        
        return VideoAnalysisResponse(
            content_item_id=content_item_id,
            status="processing",
            analysis=None,
            cached=False,
        )

