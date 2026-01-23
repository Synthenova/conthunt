import asyncio
import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.core import get_settings, logger
from app.db import get_db_connection, set_rls_user
from app.db import queries
from app.api.v1.analysis import run_gemini_analysis
from app.schemas.insights import BoardInsightsResult

settings = get_settings()

INSIGHTS_SYSTEM_PROMPT = """You are a creative strategist producing board-level insights.
Use the previous insights as a baseline and incorporate new video analyses.
Return only the structured JSON that matches the provided schema.
If there is any overlap, deduplicate and improve clarity."""


def _format_analysis_entry(media_asset_id: UUID, analysis: dict) -> str:
    hook = analysis.get("hook") or ""
    call_to_action = analysis.get("call_to_action") or ""
    on_screen_texts = analysis.get("on_screen_texts") or []
    key_topics = analysis.get("key_topics") or []
    summary = analysis.get("summary") or ""
    hashtags = analysis.get("hashtags") or []

    return "\n".join([
        f"media_asset_id: {media_asset_id}",
        f"hook: {hook}",
        f"call_to_action: {call_to_action}",
        f"on_screen_texts: {', '.join(on_screen_texts)}",
        f"key_topics: {', '.join(key_topics)}",
        f"summary: {summary}",
        f"hashtags: {', '.join(hashtags)}",
    ])


async def _ensure_video_analyses(
    user_id: UUID,
    user_role: str,
    media_asset_ids: list[UUID],
) -> list[dict]:
    """
    Ensure all video analyses exist and wait for them to complete.
    Triggers Gemini analysis for missing videos, then polls until all done (max 5 min).
    
    CRITICAL: Now charges credits for each missing video analysis via AnalysisService.
    If user runs out of credits, those specific videos will fail to analyze.
    """
    from app.services.analysis_service import analysis_service

    async with get_db_connection() as conn:
        analyses = await queries.get_video_analyses_by_media_assets(conn, media_asset_ids)

    role = user_role

    analyses_by_id = {row["media_asset_id"]: row for row in analyses}
    
    # Find truly missing analyses (no record at all)
    missing_ids = [mid for mid in media_asset_ids if mid not in analyses_by_id]

    if missing_ids:
        logger.info(f"[INSIGHTS] Triggering {len(missing_ids)} missing video analyses (Paid)")
        tasks = []
        for mid in missing_ids:
            try:
                # Trigger paid analysis - failures (e.g. limit exceeded) are logged but don't stop the batch
                tasks.append(
                    analysis_service.trigger_paid_analysis(
                        user_id=user_id,          # Pass UUID directly
                        user_role=role,
                        media_asset_id=mid,
                        background_tasks=None, # Already in bg task
                        context_source="board_insights"
                    )
                )
            except Exception as e:
                logger.error(f"[INSIGHTS] Failed to trigger analysis for {mid}: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # Poll until all analyses are done (completed/failed) or timeout
    # Max 5 min (30 attempts x 10s)
    for attempt in range(30):
        async with get_db_connection() as conn:
            analyses = await queries.get_video_analyses_by_media_assets(conn, media_asset_ids)
        
        # Check if any are still pending (queued or processing)
        pending = [
            row for row in analyses 
            if row.get("status") in ("queued", "processing")
        ]
        
        # Also check for missing (not yet created)
        analyses_by_id = {row["media_asset_id"]: row for row in analyses}
        missing = [mid for mid in media_asset_ids if mid not in analyses_by_id]
        
        if not pending and not missing:
            logger.info(f"[INSIGHTS] All {len(analyses)} video analyses complete")
            break
        
        logger.info(f"[INSIGHTS] Waiting for analyses... {len(pending)} processing, {len(missing)} missing (attempt {attempt+1}/30)")
        await asyncio.sleep(10)
    else:
        logger.warning(f"[INSIGHTS] Timeout waiting for analyses after 5 min")
    
    # Return final state
    async with get_db_connection() as conn:
        analyses = await queries.get_video_analyses_by_media_assets(conn, media_asset_ids)
    
    return analyses


async def execute_board_insights(
    board_id: UUID,
    user_id: UUID,
    user_role: str,
) -> None:
    """
    Build board-level insights based on cached video analyses.
    Triggers Gemini analysis for missing videos and retries later if needed.
    """
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)

        board = await queries.get_board_by_id(conn, board_id)
        if not board:
            logger.warning(f"[INSIGHTS] Board not found: {board_id}")
            return

        insights_row = await queries.get_board_insights(conn, board_id)
        insights_id = await queries.upsert_pending_board_insights(conn, board_id)

        previous_insights = None
        last_completed_at: Optional[datetime] = None
        if insights_row:
            previous_insights = insights_row.get("insights_result") or None
            last_completed_at = insights_row.get("last_completed_at")

        media_assets = await queries.get_board_media_assets_since(
            conn,
            board_id=board_id,
            since=last_completed_at,
        )

    if not media_assets:
        if previous_insights:
            async with get_db_connection() as conn:
                await set_rls_user(conn, user_id)
                await queries.update_board_insights_status(
                    conn,
                    insights_id=insights_id,
                    status="completed",
                    insights_result=previous_insights,
                )
            return

        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            await queries.update_board_insights_status(
                conn,
                insights_id=insights_id,
                status="failed",
                error="No videos available for insights",
            )
        return

    media_asset_ids = [row["media_asset_id"] for row in media_assets]
    analyses = await _ensure_video_analyses(
        user_id,
        user_role,
        media_asset_ids,
    )

    completed_analyses = [
        row for row in analyses
        if row.get("status") == "completed" and row.get("analysis_result")
    ]

    if not completed_analyses and not previous_insights:
        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            await queries.update_board_insights_status(
                conn,
                insights_id=insights_id,
                status="failed",
                error="No completed analyses available",
            )
        return

    if not completed_analyses and previous_insights:
        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            await queries.update_board_insights_status(
                conn,
                insights_id=insights_id,
                status="completed",
                insights_result=previous_insights,
            )
        return

    analysis_blocks = [
        _format_analysis_entry(row["media_asset_id"], row["analysis_result"])
        for row in completed_analyses
    ]

    previous_insights_text = (
        json.dumps(previous_insights, ensure_ascii=True, indent=2)
        if previous_insights
        else "None"
    )

    human_message = HumanMessage(
        content="\n\n".join([
            f"Previous insights:\n{previous_insights_text}",
            "New video analyses:",
            "\n\n".join(analysis_blocks),
        ])
    )

    system_message = SystemMessage(content=INSIGHTS_SYSTEM_PROMPT)

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0.4,
        api_key=settings.GOOGLE_API_KEY,
    )
    structured_llm = llm.with_structured_output(BoardInsightsResult)

    # Allow exceptions to bubble up for Cloud Tasks retry
    result: BoardInsightsResult = await structured_llm.ainvoke([system_message, human_message])
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        await queries.update_board_insights_status(
            conn,
            insights_id=insights_id,
            status="completed",
            insights_result=result.model_dump(),
            last_completed_at=datetime.utcnow(),
        )
