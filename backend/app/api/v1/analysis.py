import logging
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

from app.auth.firebase import get_current_user
from app.db.session import get_db_connection
from app.db.queries.twelvelabs import (
    get_video_analysis_by_content_item,
    insert_video_analysis,
    get_content_item_by_id
)
from app.schemas.analysis import VideoAnalysisResponse, VideoAnalysisResult
from app.services.twelvelabs_processing import process_twelvelabs_indexing

load_dotenv()

logger = logging.getLogger(__name__)
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

@router.post(
    "/video-analysis/{content_item_id}",
    response_model=VideoAnalysisResponse,
    summary="Analyze video with Gemini 3 Flash",
)
async def analyze_video(
    content_item_id: UUID,
    background_tasks: BackgroundTasks,
    _user: dict = Depends(get_current_user),
):
    """
    Analyze a video using Google Gemini 3 Flash Preview.
    Triggers 12Labs indexing in the background.
    """
    logger.info(f"Starting Gemini analysis for {content_item_id}")
    
    # Trigger 12Labs Indexing in Background
    background_tasks.add_task(process_twelvelabs_indexing, content_item_id)
    
    async with get_db_connection() as conn:
        # 1. Check cache
        existing = await get_video_analysis_by_content_item(conn, content_item_id)
        if existing:
            return VideoAnalysisResponse(
                id=existing["id"],
                content_item_id=existing["content_item_id"],
                status="completed",
                analysis=VideoAnalysisResult(**existing["analysis_result"]),
                created_at=existing["created_at"],
                cached=True,
            )

        # 2. Get Content Item & URI
        item = await get_content_item_by_id(conn, content_item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Content item not found")
            
        # Prefer GCS URI, fall back to video_url
        video_uri = item.get("video_gcs_uri") or item.get("video_url")
        if not video_uri:
            raise HTTPException(status_code=400, detail="No video URL available for analysis")

        logger.info(f"Using video URI: {video_uri}")

    # 3. Call LLM (outside DB transaction to avoid holding connection)
    try:
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
        
        # Async invoke
        result: VideoAnalysisResult = await structured_llm.ainvoke([message])
        
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # 4. Save Result
    async with get_db_connection() as conn:
        # Double check cache race
        existing = await get_video_analysis_by_content_item(conn, content_item_id)
        if existing:
             return VideoAnalysisResponse(
                id=existing["id"],
                content_item_id=existing["content_item_id"],
                status="completed",
                analysis=VideoAnalysisResult(**existing["analysis_result"]),
                created_at=existing["created_at"],
                cached=True,
            )

        analysis_id = await insert_video_analysis(
            conn,
            content_item_id=content_item_id,
            twelvelabs_asset_id=None, # Not using TwelveLabs asset
            prompt=DEFAULT_ANALYSIS_PROMPT,
            analysis_result=result.model_dump(),
            token_usage=0, # We don't get usage easily from structured output wrapper yet, or ignore
        )
        await conn.commit()

        return VideoAnalysisResponse(
            id=analysis_id,
            content_item_id=content_item_id,
            status="completed",
            analysis=result,
            created_at=datetime.utcnow(),
            cached=False
        )
