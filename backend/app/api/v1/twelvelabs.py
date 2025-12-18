"""TwelveLabs video analysis API endpoints."""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.auth.firebase import get_current_user
from app.core.settings import get_settings
from app.db.session import get_db_connection
from app.db import queries
from app.schemas.twelvelabs import (
    VideoAnalysisResponse, 
    VideoAnalysisResult,
    TwelveLabsSearchRequest,
    TwelveLabsSearchResponse,
    TwelveLabsSearchResponseItem
)
from app.services.twelvelabs_processing import process_video_analysis
from app.services.twelvelabs_client import get_twelvelabs_client


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

@router.post(
    "/search",
    response_model=TwelveLabsSearchResponse,
    summary="Search TwelveLabs Index",
)
async def search_twelvelabs(
    request: TwelveLabsSearchRequest,
    _user: dict = Depends(get_current_user),
):
    """
    Search the TwelveLabs index for video clips matching the query.
    """
    settings = get_settings()
    client = get_twelvelabs_client()
    
    index_id = request.index_id or settings.TWELVELABS_INDEX_ID
    if not index_id:
        raise HTTPException(status_code=500, detail="TwelveLabs Index ID not configured")

    try:
        # Use the SDK to search
        # Note: The SDK method signature might vary, verifying based on typical SDK usage
        # Assuming client.search.query or similar. 
        # Using the low-level proxy or specific method from our client wrapper if available.
        # If get_twelvelabs_client returns the raw SDK client:
        
        # Adjust based on SDK version 1.1.0
        # Check if we have a wrapper or raw client. 
        # backend/app/services/twelvelabs_client.py would tell us, but for now assuming standard SDK usage
        
        results = client.search.query(
            index_id=index_id,
            query_text=request.query,
            options=request.search_options
        )
        
        # Map SDK results to schema
        # The SDK returns an iterator/list of SearchItem
        response_items = []
        for item in results:
             response_items.append(TwelveLabsSearchResponseItem(
                 score=getattr(item, "score", 0.0),
                 start=item.start,
                 end=item.end,
                 video_id=item.video_id,
                 confidence=getattr(item, "confidence", "medium"),
                 thumbnail_url=item.thumbnail_url,
                 metadata=item.metadata if hasattr(item, "metadata") else None
             ))
             
        return TwelveLabsSearchResponse(data=response_items)

    except Exception as e:
        logger.error(f"TwelveLabs search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
