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
    create_pending_analysis,
    update_analysis_status,
)
from app.db.queries.content import get_media_asset_by_id
from app.schemas.analysis import VideoAnalysisResponse, VideoAnalysisResult
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset

load_dotenv()

router = APIRouter(tags=["video-analysis"])

# Initialize Gemini Model
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0.7,
    project='conthunt-dev',
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
    """
    import time
    import traceback
    
    start_time = time.time()
    print(f"[ANALYSIS] Starting background task for media_asset_id={media_asset_id}, analysis_id={analysis_id}")
    print(f"[ANALYSIS] Video URI: {video_uri}")
    
    try:
        print(f"[ANALYSIS] Building HumanMessage with video...")
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
        
        print(f"[ANALYSIS] Invoking Gemini LLM (structured output)...")
        invoke_start = time.time()
        result: VideoAnalysisResult = await structured_llm.ainvoke([message])
        invoke_duration = time.time() - invoke_start
        print(f"[ANALYSIS] Gemini LLM returned in {invoke_duration:.2f}s")
        print(f"[ANALYSIS] Result summary: {result.summary[:100] if result.summary else 'N/A'}...")
        
        # Update to completed
        print(f"[ANALYSIS] Updating status to 'completed'...")
        async with get_db_connection() as conn:
            await update_analysis_status(
                conn,
                analysis_id=analysis_id,
                status="completed",
                analysis_result=result.model_dump(),
            )
            await conn.commit()
        
        total_duration = time.time() - start_time
        print(f"[ANALYSIS] ✅ Completed analysis for media_asset {media_asset_id} in {total_duration:.2f}s total")
        
    except Exception as e:
        total_duration = time.time() - start_time
        logger.error(f"[ANALYSIS] ❌ Failed for media_asset {media_asset_id} after {total_duration:.2f}s: {type(e).__name__}: {e}")
        logger.error(f"[ANALYSIS] Traceback:\n{traceback.format_exc()}")
        
        # Update to failed
        try:
            async with get_db_connection() as conn:
                await update_analysis_status(
                    conn,
                    analysis_id=analysis_id,
                    status="failed",
                    error=str(e),
                )
                await conn.commit()
            print(f"[ANALYSIS] Updated status to 'failed' for {analysis_id}")
        except Exception as db_err:
            logger.error(f"[ANALYSIS] Failed to update status to 'failed': {db_err}")


async def run_gemini_analysis(media_asset_id: UUID, background_tasks: BackgroundTasks) -> VideoAnalysisResponse:
    """
    Non-blocking Gemini analysis - returns immediately.
    Creates 'processing' record and spawns background task.
    Does NOT trigger TwelveLabs indexing.
    """
    print(f"run_gemini_analysis called for media_asset {media_asset_id}")
    
    async with get_db_connection() as conn:
        # 1. Get media asset details
        media_asset = await get_media_asset_by_id(conn, media_asset_id)
        if not media_asset:
            raise HTTPException(status_code=404, detail="Media asset not found")
        
        video_uri = media_asset.get("gcs_uri") or media_asset.get("video_url")
        
        if not video_uri:
            raise HTTPException(status_code=400, detail="No video URL available for analysis")
        
        # 2. Check if analysis exists (any status) for this media_asset
        existing = await get_video_analysis_by_media_asset(conn, media_asset_id)
        if existing:
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

        # 3. Create pending analysis record
        analysis_id = await create_pending_analysis(
            conn,
            media_asset_id=media_asset_id,
            prompt=DEFAULT_ANALYSIS_PROMPT,
        )
        await conn.commit()
        
        print(f"Created pending analysis {analysis_id} for media_asset {media_asset_id}")

        # 4. Spawn background task for LLM processing
        print(f"[ANALYSIS] Spawning background task for analysis_id={analysis_id}")
        import asyncio
        asyncio.create_task(_execute_gemini_analysis(analysis_id, media_asset_id, video_uri))
        print(f"[ANALYSIS] Background task spawned successfully")
        
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
    """
    # Trigger 12Labs Indexing in Background
    background_tasks.add_task(process_twelvelabs_indexing_by_media_asset, media_asset_id)
    
    # Run non-blocking Gemini analysis
    return await run_gemini_analysis(media_asset_id, background_tasks)
