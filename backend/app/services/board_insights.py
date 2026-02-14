import asyncio
import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage

from app.core import get_settings, logger
from app.agent.model_factory import init_chat_model
from app.db import get_db_connection, set_rls_user
from app.db import queries
from app.api.v1.analysis import run_gemini_analysis
from app.schemas.insights import BoardInsightsResult
from app.llm.context import set_llm_context

settings = get_settings()

BATCH_INSIGHTS_PROMPT = """Analyze these video analyses and extract key patterns, themes, and insights.
Return structured insights based on what you observe across these videos."""

MERGE_INSIGHTS_PROMPT = """You are merging multiple insight sets into one cohesive board-level insight.
Combine, deduplicate, and synthesize the patterns from all provided insights.
Return only the structured JSON matching the schema."""


def _format_analysis_entry(media_asset_id: UUID, analysis: dict) -> str:
    """Format a single analysis for the insights prompt - uses markdown string."""
    markdown = analysis.get("analysis", "")
    return f"### Video: {media_asset_id}\n\n{markdown}"


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


async def _process_single_batch(
    batch: list[dict],
    user_id: UUID,
    llm,
) -> dict:
    """Process a single batch of analyses → insights (no prev insights)."""
    analysis_blocks = [
        _format_analysis_entry(row["media_asset_id"], row["analysis_result"])
        for row in batch
    ]
    
    human_message = HumanMessage(content="\n\n".join(analysis_blocks))
    system_message = SystemMessage(content=BATCH_INSIGHTS_PROMPT)
    
    structured_llm = llm.with_structured_output(BoardInsightsResult)
    with set_llm_context(user_id=str(user_id), route="insights.batch"):
        result: BoardInsightsResult = await structured_llm.ainvoke([system_message, human_message])
    
    return result.model_dump()


async def _generate_parallel_insights(
    completed_analyses: list[dict],
    previous_insights: dict | None,
    user_id: UUID,
) -> BoardInsightsResult:
    """
    1. Split into batches of 10
    2. Run all batches in PARALLEL → each produces insights
    3. Merge all batch insights + prev insights → final insights
    """
    BATCH_SIZE = 10
    llm = init_chat_model("openrouter/google/gemini-3-flash-preview", temperature=0.4)
    
    # Split into batches
    batches = [
        completed_analyses[i:i + BATCH_SIZE]
        for i in range(0, len(completed_analyses), BATCH_SIZE)
    ]
    
    logger.info(f"[INSIGHTS] Processing {len(completed_analyses)} analyses in {len(batches)} parallel batches")
    
    # Run all batches in parallel
    batch_tasks = [
        _process_single_batch(batch, user_id, llm)
        for batch in batches
    ]
    batch_insights = await asyncio.gather(*batch_tasks)
    
    # Collect all insights to merge (previous + all batch results)
    all_insights = []
    if previous_insights:
        all_insights.append(previous_insights)
    all_insights.extend(batch_insights)
    
    # If only one insight set, return it directly
    if len(all_insights) == 1:
        return BoardInsightsResult(**all_insights[0])
    
    # Merge all insights into final
    logger.info(f"[INSIGHTS] Merging {len(all_insights)} insight sets into final result")
    insights_text = "\n\n---\n\n".join([
        f"Insight Set {i+1}:\n{json.dumps(ins, indent=2)}"
        for i, ins in enumerate(all_insights)
    ])
    
    human_message = HumanMessage(content=insights_text)
    system_message = SystemMessage(content=MERGE_INSIGHTS_PROMPT)
    
    structured_llm = llm.with_structured_output(BoardInsightsResult)
    with set_llm_context(user_id=str(user_id), route="insights.merge"):
        final: BoardInsightsResult = await structured_llm.ainvoke([system_message, human_message])
    
    return final


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

    # Generate insights using parallel batch processing
    result = await _generate_parallel_insights(
        completed_analyses=completed_analyses,
        previous_insights=previous_insights,
        user_id=user_id,
    )
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        await queries.update_board_insights_status(
            conn,
            insights_id=insights_id,
            status="completed",
            insights_result=result.model_dump(),
            last_completed_at=datetime.utcnow(),
        )

