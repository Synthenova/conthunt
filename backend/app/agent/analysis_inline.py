"""Inline Gemini analysis for agent tools (no polling)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Any, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from app.core import get_settings, logger
from app.db.session import get_db_connection
from app.db.queries.analysis import (
    get_video_analysis_by_media_asset,
    create_pending_analysis,
    update_analysis_status,
)
from app.db.queries.content import get_media_asset_by_id
from app.schemas.analysis import VideoAnalysisResult

settings = get_settings()

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0.7,
    project=settings.GCLOUD_PROJECT,
    vertexai=True,
)

structured_llm = llm.with_structured_output(VideoAnalysisResult)

DEFAULT_ANALYSIS_PROMPT = """Analyze this video and extract the following information:
1. Hook: The attention-grabbing opening (first 3 seconds)
2. Call to Action: Any requests for viewer engagement (subscribe, like, follow, etc.)
3. On-screen texts: Any text overlays or captions shown in the video
4. Key topics: Main subjects or themes discussed
5. Summary: A brief 2-3 sentence summary of the video content
6. Hashtags: Suggested hashtags for this content

Be specific and extract actual content from the video, not generic descriptions."""


def _resolve_video_uri(media_asset: Dict[str, Any]) -> str | None:
    source_url = media_asset.get("source_url", "") or ""
    gcs_uri = media_asset.get("gcs_uri")
    is_youtube = "youtube.com" in source_url or "youtu.be" in source_url
    if is_youtube:
        return source_url
    return gcs_uri or media_asset.get("video_url") or source_url


async def run_inline_video_analysis(media_asset_id: UUID) -> Dict[str, Any]:
    """
    Run Gemini analysis inline and persist status/result.
    Returns completed analysis or cached result without polling.
    """
    try:
        async with get_db_connection() as conn:
            media_asset = await get_media_asset_by_id(conn, media_asset_id)
            if not media_asset:
                return {"error": "Media asset not found"}

            existing = await get_video_analysis_by_media_asset(conn, media_asset_id)
            if existing and existing.get("status") == "completed" and existing.get("analysis_result"):
                return {
                    "id": existing["id"],
                    "media_asset_id": media_asset_id,
                    "status": "completed",
                    "analysis": existing["analysis_result"],
                    "error": existing.get("error"),
                    "created_at": existing.get("created_at"),
                    "cached": True,
                }

            if existing:
                analysis_id = existing["id"]
                await update_analysis_status(conn, analysis_id=analysis_id, status="processing")
            else:
                analysis_id = await create_pending_analysis(
                    conn,
                    media_asset_id=media_asset_id,
                    prompt=DEFAULT_ANALYSIS_PROMPT,
                )
            await conn.commit()

        video_uri = _resolve_video_uri(media_asset)
        if not video_uri:
            return {"error": "No video URL available for analysis"}

        message = HumanMessage(
            content=[
                {"type": "text", "text": DEFAULT_ANALYSIS_PROMPT},
                {"type": "media", "file_uri": video_uri, "mime_type": "video/mp4"},
            ]
        )

        logger.info("[AGENT TOOL] Running Gemini analysis inline for %s", media_asset_id)
        result: VideoAnalysisResult = await structured_llm.ainvoke([message])

        async with get_db_connection() as conn:
            await update_analysis_status(
                conn,
                analysis_id=analysis_id,
                status="completed",
                analysis_result=result.model_dump(),
            )
            await conn.commit()

        return {
            "id": analysis_id,
            "media_asset_id": media_asset_id,
            "status": "completed",
            "analysis": result.model_dump(),
            "error": None,
            "created_at": existing.get("created_at") if existing else datetime.utcnow(),
            "cached": False,
        }
    except Exception as exc:
        logger.exception("[AGENT TOOL] Inline analysis error for %s", media_asset_id)
        try:
            async with get_db_connection() as conn:
                if "analysis_id" in locals():
                    await update_analysis_status(
                        conn,
                        analysis_id=analysis_id,
                        status="failed",
                        error=str(exc),
                    )
                    await conn.commit()
        except Exception:
            logger.exception("[AGENT TOOL] Failed to update analysis status after error")
        return {"error": f"Analysis error: {str(exc)}"}
