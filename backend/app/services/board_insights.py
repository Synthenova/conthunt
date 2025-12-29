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
from app.services.cloud_tasks import cloud_tasks

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
    media_asset_ids: list[UUID],
) -> tuple[list[dict], bool]:
    """
    Fetch cached analyses for media assets.
    If any analyses are missing, trigger Gemini analysis in background.
    Returns (analysis_rows, has_pending).
    """
    async with get_db_connection() as conn:
        analyses = await queries.get_video_analyses_by_media_assets(conn, media_asset_ids)

    analyses_by_id = {row["media_asset_id"]: row for row in analyses}
    missing_ids = [mid for mid in media_asset_ids if mid not in analyses_by_id]

    if missing_ids:
        tasks = [
            run_gemini_analysis(
                media_asset_id=mid,
                background_tasks=None,
                use_cloud_tasks=True,
            )
            for mid in missing_ids
        ]
        await _gather_safely(tasks)

    has_pending = bool(missing_ids)
    for row in analyses:
        if row.get("status") == "processing":
            has_pending = True

    return analyses, has_pending


async def _gather_safely(tasks: list) -> None:
    import asyncio
    if not tasks:
        return
    await asyncio.gather(*tasks, return_exceptions=True)


async def execute_board_insights(
    board_id: UUID,
    user_id: UUID,
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
    analyses, has_pending = await _ensure_video_analyses(media_asset_ids)

    completed_analyses = [
        row for row in analyses
        if row.get("status") == "completed" and row.get("analysis_result")
    ]

    if has_pending:
        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            await queries.update_board_insights_status(
                conn,
                insights_id=insights_id,
                status="processing",
            )
        await cloud_tasks.create_http_task(
            queue_name=settings.QUEUE_GEMINI,
            relative_uri="/v1/tasks/boards/insights",
            payload={"board_id": str(board_id), "user_id": str(user_id)},
            schedule_seconds=120,
        )
        return

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
        project=settings.GCLOUD_PROJECT,
        vertexai=True,
    )
    structured_llm = llm.with_structured_output(BoardInsightsResult)

    try:
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
    except Exception as exc:
        logger.error(f"[INSIGHTS] Failed to build insights for {board_id}: {exc}", exc_info=True)
        async with get_db_connection() as conn:
            await set_rls_user(conn, user_id)
            await queries.update_board_insights_status(
                conn,
                insights_id=insights_id,
                status="failed",
                error=str(exc),
            )
