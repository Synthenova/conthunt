import logging
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

from app.core import logger
from app.auth.firebase import get_current_user
from app.db.session import get_db_connection
from app.db.queries.analysis import (
    get_video_analysis_by_media_asset,
    update_analysis_status,
)
from app.db.queries.content import get_media_asset_by_id
from app.schemas.analysis import VideoAnalysisResponse, VideoAnalysisResult
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
from app.services.cloud_tasks import cloud_tasks
from app.core import get_settings

settings = get_settings()

load_dotenv()

router = APIRouter(tags=["video-analysis"])

# Initialize Gemini Model
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0.7,
    project=settings.GCP_PROJECT,
    vertexai=True
)

# Bind Structured Output
structured_llm = llm.with_structured_output(VideoAnalysisResult)

DEFAULT_ANALYSIS_PROMPT = """Analyze this video and extract the following information:
1. Hook: The attention-grabbing opening (first 3 seconds)
2. Call to Action: Any requests for viewer engagement (subscribe, like, follow, etc.)
3. On-screen texts: Any text overlays or captions shown in the video
4. Key topics: Main subjects or themes discussed
5. Summary: A brief 2-3 sentence summary of the video content
6. Hashtags: Suggested hashtags for this content

Be specific and extract actual content from the video, not generic descriptions."""


async def _execute_gemini_analysis(analysis_id: UUID, media_asset_id: UUID, video_uri: str) -> None:
    """
    Background task: Run Gemini LLM and update analysis status.
    Called after creating a 'processing' record.
    Exceptions are propagated to allow Cloud Tasks retries.
    """
    import time
    import traceback
    
    start_time = time.time()
    logger.info(f"[ANALYSIS] Starting background task for media_asset_id={media_asset_id}, analysis_id={analysis_id}")
    logger.info(f"[ANALYSIS] Video URI: {video_uri}")
    
    try:
        # 1. Build Message
        logger.info(f"[ANALYSIS] Building HumanMessage with video...")
        message = HumanMessage(
            content=[
                {"type": "text", "text": DEFAULT_ANALYSIS_PROMPT},
                {      
                    "type": "media",              
                    "file_uri": video_uri,
                    "mime_type": "video/mp4", 
                }
            ]
        )
        
        # 2. Invoke LLM
        logger.info(f"[ANALYSIS] Invoking Gemini LLM (structured output)...")
        invoke_start = time.time()
        result: VideoAnalysisResult = await structured_llm.ainvoke([message])
        invoke_duration = time.time() - invoke_start
        
        logger.info(f"[ANALYSIS] Gemini LLM returned in {invoke_duration:.2f}s")
        logger.info(f"[ANALYSIS] Result summary: {result.summary[:100] if result.summary else 'N/A'}...")
        
        # 3. Update to completed
        logger.info(f"[ANALYSIS] Updating status to 'completed'...")
        async with get_db_connection() as conn:
            await update_analysis_status(
                conn,
                analysis_id=analysis_id,
                status="completed",
                analysis_result=result.model_dump(),
            )
            await conn.commit()
        
        total_duration = time.time() - start_time
        logger.info(f"[ANALYSIS] ✅ Completed analysis for media_asset {media_asset_id} in {total_duration:.2f}s total")
    
    except Exception as e:
        # Mark as failed so insights don't get stuck waiting
        logger.error(f"[ANALYSIS] ❌ Failed analysis for media_asset {media_asset_id}: {e}")
        logger.error(traceback.format_exc())
        try:
            async with get_db_connection() as conn:
                await update_analysis_status(
                    conn,
                    analysis_id=analysis_id,
                    status="failed",
                    error=str(e),
                )
                await conn.commit()
        except Exception as db_err:
            logger.error(f"[ANALYSIS] Failed to update status to failed: {db_err}")
        # Re-raise for Cloud Tasks retry mechanism
        raise


async def run_gemini_analysis(
    media_asset_id: UUID, 
    background_tasks: BackgroundTasks | None = None,
    use_cloud_tasks: bool = True
) -> VideoAnalysisResponse:
    """
    Unified Gemini analysis entry point.
    
    1. Atomically claims or retrieves existing analysis (prevents race conditions).
    2. Checks media asset status and dispatches priority download if needed.
    3. Spawns background task for LLM processing.
    4. Returns immediately with current status.
    """
    from app.db.queries.analysis import claim_or_create_analysis
    
    logger.info(f"run_gemini_analysis called for media_asset {media_asset_id}")
    
    async with get_db_connection() as conn:
        # 1. Get media asset details
        media_asset = await get_media_asset_by_id(conn, media_asset_id)
        if not media_asset:
            raise HTTPException(status_code=404, detail="Media asset not found")
        
        # Determine video URI for analysis
        source_url = media_asset.get("source_url", "")
        gcs_uri = media_asset.get("gcs_uri")
        asset_status = media_asset.get("status", "pending")
        
        # For YouTube, always use source_url (gcs_uri is not a real video file)
        is_youtube = "youtube.com" in source_url or "youtu.be" in source_url
        if is_youtube:
            video_uri = source_url
        else:
            video_uri = gcs_uri or media_asset.get("video_url") or source_url
        
        if not video_uri:
            raise HTTPException(status_code=400, detail="No video URL available for analysis")
        
        # 2. Atomically claim or create analysis (prevents race conditions)
        analysis_id, status, was_created = await claim_or_create_analysis(
            conn,
            media_asset_id=media_asset_id,
            prompt=DEFAULT_ANALYSIS_PROMPT,
        )
        await conn.commit()
        
        # If existing analysis is completed, return cached result
        if status == "completed":
            existing = await get_video_analysis_by_media_asset(conn, media_asset_id)
            analysis = None
            if existing and existing.get("analysis_result"):
                analysis = VideoAnalysisResult(**existing["analysis_result"])
            return VideoAnalysisResponse(
                id=analysis_id,
                media_asset_id=media_asset_id,
                status="completed",
                analysis=analysis,
                error=existing.get("error") if existing else None,
                created_at=existing["created_at"] if existing else datetime.utcnow(),
                cached=True,
            )
        
        # If already processing/queued, just return status (task already running)
        if status in ("processing", "queued") and not was_created:
            return VideoAnalysisResponse(
                id=analysis_id,
                media_asset_id=media_asset_id,
                status=status,
                analysis=None,
                created_at=datetime.utcnow(),
                cached=True,
            )
        
        logger.info(f"Created/claimed analysis {analysis_id} for media_asset {media_asset_id}")

    # 3. Check if we need to prioritize the media download
    # Only dispatch priority download if asset is 'pending' (not yet claimed by any downloader)
    if not is_youtube and asset_status == "pending":
        logger.info(f"[PRIORITY] Asset {media_asset_id} is pending, dispatching priority download")
        # Get content item info for the download task
        platform = media_asset.get("platform", "unknown")
        # Get external_id from content_item
        async with get_db_connection() as conn:
            from sqlalchemy import text
            result = await conn.execute(
                text("""
                    SELECT ci.platform, ci.external_id
                    FROM content_items ci
                    JOIN media_assets ma ON ma.content_item_id = ci.id
                    WHERE ma.id = :asset_id
                """),
                {"asset_id": media_asset_id}
            )
            row = result.fetchone()
            if row:
                platform, external_id = row[0], row[1]
            else:
                platform, external_id = "unknown", "unknown"
        
        await cloud_tasks.create_http_task(
            queue_name=settings.QUEUE_MEDIA_DOWNLOAD_PRIORITY,
            relative_uri="/v1/tasks/media/download",
            payload={
                "asset_id": str(media_asset_id),
                "platform": platform,
                "external_id": external_id,
                "priority": True,  # Signal for local handler to skip semaphore
            }
        )

    # 4. Spawn background task for LLM processing
    logger.info(f"[ANALYSIS] Spawning background task for analysis_id={analysis_id}")
    
    if use_cloud_tasks or not background_tasks:
        logger.info(f"[ANALYSIS] Using Cloud Tasks (queue={settings.QUEUE_GEMINI}) for analysis {analysis_id}")
        await cloud_tasks.create_http_task(
            queue_name=settings.QUEUE_GEMINI,
            relative_uri="/v1/tasks/gemini/analyze",
            payload={
                "analysis_id": str(analysis_id),
                "media_asset_id": str(media_asset_id),
                "video_uri": video_uri
            }
        )
    else:
        # Legacy/Local mode (fallback)
        import asyncio
        asyncio.create_task(_execute_gemini_analysis(analysis_id, media_asset_id, video_uri))
        logger.info(f"[ANALYSIS] Background task spawned successfully (local asyncio)")
    
    # 5. Return immediately with processing status
    return VideoAnalysisResponse(
        id=analysis_id,
        media_asset_id=media_asset_id,
        status="processing",
        analysis=None,
        created_at=datetime.utcnow(),
        cached=False,
    )


@router.post(
    "/video-analysis/{media_asset_id}",
    response_model=VideoAnalysisResponse,
    summary="Analyze video with Gemini 3 Flash",
)
async def analyze_video(
    media_asset_id: UUID,
    background_tasks: BackgroundTasks,
    _user: dict = Depends(get_current_user),
):
    """
    Analyze a video using Google Gemini 3 Flash Preview.
    Returns immediately with 'processing' status. Poll to check completion.
    Also triggers 12Labs indexing in the background.
    
    Credit is charged per-user on first access, regardless of global cache state.
    Note: Requires db_user_id in JWT. Users without it will get 401.
    """
    from app.services.analysis_service import analysis_service
    
    user_id = _user["db_user_id"]
    
    # Check if this is a YouTube video (TwelveLabs can't handle YouTube URLs directly)
    async with get_db_connection() as conn:
        media_asset = await get_media_asset_by_id(conn, media_asset_id)
    
    source_url = media_asset.get("source_url", "") if media_asset else ""
    is_youtube = "youtube.com" in source_url or "youtu.be" in source_url    
    
    if not is_youtube:
        # Trigger 12Labs Indexing in Background (only for non-YouTube)
        await cloud_tasks.create_http_task(
            queue_name=settings.QUEUE_TWELVELABS,
            relative_uri="/v1/tasks/twelvelabs/index",
            payload={"media_asset_id": str(media_asset_id)}
        )
    
    # Use centralized service to enforce credit consumption
    return await analysis_service.trigger_paid_analysis(
        user_id=user_id,
        user_role=_user["role"],
        media_asset_id=media_asset_id,
        background_tasks=background_tasks,
        context_source="api_endpoint"
    )


@router.get(
    "/video-analysis/{media_asset_id}",
    response_model=VideoAnalysisResponse,
    summary="Get existing video analysis (read-only)",
)
async def get_video_analysis(
    media_asset_id: UUID,
    _user: dict = Depends(get_current_user),
):
    """
    Get existing video analysis if the user has already accessed it.
    Does NOT trigger new analysis or charge credits.
    Returns 404 if user hasn't accessed this analysis before.
    """
    from app.db.queries.analysis import has_user_accessed_analysis
    from app.db import set_rls_user
    
    user_id = _user["db_user_id"]
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        
        # Check if user has accessed this analysis
        user_accessed = await has_user_accessed_analysis(conn, user_id, media_asset_id)
        if not user_accessed:
            raise HTTPException(status_code=404, detail="Analysis not found for this user")
        
        # Get the cached analysis
        existing = await get_video_analysis_by_media_asset(conn, media_asset_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        status = existing.get("status", "completed")
        analysis = None
        if status == "completed" and existing.get("analysis_result"):
            analysis = VideoAnalysisResult(**existing["analysis_result"])
        
        return VideoAnalysisResponse(
            id=existing["id"],
            media_asset_id=media_asset_id,
            status=status,
            analysis=analysis,
            error=existing.get("error"),
            created_at=existing["created_at"],
            cached=True,
        )
