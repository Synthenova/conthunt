import logging
import asyncio
from uuid import UUID
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from langchain_core.messages import HumanMessage
from app.integrations.posthog_client import capture_event
from dotenv import load_dotenv
from sqlalchemy import text

from app.core import logger
from app.auth.firebase import get_current_user
from app.db.session import get_db_connection
from app.db import set_rls_user
from app.agent.model_factory import init_chat_model
from app.db.queries.analysis import (
    claim_or_create_analyses_batch,
    get_video_analysis_by_media_asset,
    get_video_analyses_by_media_assets,
    rescue_stale_or_failed_analyses_batch,
    update_analysis_status,
)
from app.db.queries.content import (
    get_media_asset_by_id,
    get_media_asset_download_info_by_ids,
    get_media_assets_by_ids,
)
from app.schemas.analysis import VideoAnalysisResponse
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
from app.services.cloud_tasks import cloud_tasks
from app.core import get_settings
from app.prompts.video_analysis import DEFAULT_ANALYSIS_PROMPT
from app.llm.context import set_llm_context

settings = get_settings()

load_dotenv()

router = APIRouter(tags=["video-analysis"])

# Non-YouTube analysis path: Google provider model (existing behavior).
llm = init_chat_model("google/gemini-2.5-flash-lite-preview-09-2025", temperature=0.7)

# YouTube analysis path: OpenRouter + Google AI Studio provider pin.
youtube_llm = init_chat_model(
    "openrouter/google/gemini-2.5-flash-lite-preview-09-2025",
    temperature=0.7,
    llm_init_kwargs={
        "extra_body": {"provider": {"only": ["Google AI Studio"]}},
    },
)



async def _execute_gemini_analysis(
    analysis_id: UUID,
    media_asset_id: UUID,
    video_uri: str,
    chat_id: str | None = None,
    user_id: str | None = None,
    dispatched_at: float | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """
    Background task: Run Gemini LLM and update analysis status.
    Called after creating a 'processing' record.
    Exceptions are propagated to allow Cloud Tasks retries.
    """
    import time
    import traceback
    
    start_time = time.time()
    logger.info(f"[ANALYSIS] Starting background task for media_asset_id={media_asset_id}, analysis_id={analysis_id}")
    logger.info(f"[ANALYSIS] Video URI: {video_uri[:100]}...")
    
    queue_duration_ms = 0
    if dispatched_at:
        queue_duration_ms = int((start_time - dispatched_at) * 1000)

    # Telemetry: Analysis Started
    capture_event(
        distinct_id=str(user_id) if user_id else "system",
        event="analysis_started",
        properties={
            "analysis_id": str(analysis_id),
            "media_asset_id": str(media_asset_id),
            "queue_duration_ms": queue_duration_ms,
        }
    )
    
    try:
        is_youtube = "youtube.com" in video_uri or "youtu.be" in video_uri

        # 1. Build message in provider-specific format.
        logger.info("[ANALYSIS] Building HumanMessage with video (is_youtube=%s)...", is_youtube)
        if is_youtube:
            message = HumanMessage(
                content=[
                    {"type": "text", "text": DEFAULT_ANALYSIS_PROMPT},
                    {
                        "type": "video_url",
                        "video_url": {"url": video_uri},
                    },
                ]
            )
            invoke_llm = youtube_llm
        else:
            message = HumanMessage(
                content=[
                    {"type": "text", "text": DEFAULT_ANALYSIS_PROMPT},
                    {
                        "type": "media",
                        "file_uri": video_uri,
                        "mime_type": "video/mp4",
                    },
                ]
            )
            invoke_llm = llm
        
        # 2. Invoke LLM (plain text output - markdown)
        logger.info(f"[ANALYSIS] Invoking Gemini LLM (markdown output)...")
        invoke_start = time.time()

        with set_llm_context(user_id=user_id, route="analysis.video"):
            response = await invoke_llm.ainvoke([message],)
        
        analysis_markdown = response.content
        invoke_duration = time.time() - invoke_start
        
        logger.info(f"[ANALYSIS] Gemini LLM returned in {invoke_duration:.2f}s")
        logger.info(f"[ANALYSIS] Result preview: {analysis_markdown[:200]}...")
        
        # 3. Update to completed - save as {"analysis": markdown_string}
        if persist:
            logger.info(f"[ANALYSIS] Updating status to 'completed'...")
            async with get_db_connection() as conn:
                await update_analysis_status(
                    conn,
                    analysis_id=analysis_id,
                    status="completed",
                    analysis_result={"analysis": analysis_markdown},
                )
                await conn.commit()

        total_duration = time.time() - start_time
        
        # Telemetry: Analysis Completed
        total_duration_ms = int(total_duration * 1000)
        capture_event(
            distinct_id=str(user_id) if user_id else "system",
            event="analysis_completed",
            properties={
                "analysis_id": str(analysis_id),
                "media_asset_id": str(media_asset_id),
                "duration_ms": total_duration_ms,
                "total_duration_ms": total_duration_ms + queue_duration_ms,
                "queue_duration_ms": queue_duration_ms,
                "success": True,
            }
        )

        logger.info(f"[ANALYSIS] ✅ Completed analysis for media_asset {media_asset_id} in {total_duration:.2f}s total")
        return {"analysis": analysis_markdown}
    
    except Exception as e:
        # Mark as failed so insights don't get stuck waiting
        logger.error(f"[ANALYSIS] ❌ Failed analysis for media_asset {media_asset_id} (URL: {video_uri}): {e}")
        logger.error(traceback.format_exc())
        try:
            if persist:
                async with get_db_connection() as conn:
                    await update_analysis_status(
                        conn,
                        analysis_id=analysis_id,
                        status="failed",
                        error=f"{e} (URL: {video_uri})",
                    )
                    await conn.commit()

            # Telemetry: Analysis Failed
            total_duration_ms = int((time.time() - start_time) * 1000)
            capture_event(
                distinct_id=str(user_id) if user_id else "system",
                event="analysis_completed",
                properties={
                    "analysis_id": str(analysis_id),
                    "media_asset_id": str(media_asset_id),
                    "duration_ms": total_duration_ms,
                    "total_duration_ms": total_duration_ms + queue_duration_ms,
                    "queue_duration_ms": queue_duration_ms,
                    "success": False,
                    "error": str(e),
                }
            )
        except Exception as db_err:
            logger.error(f"[ANALYSIS] Failed to update status to failed: {db_err}")
        # Re-raise for Cloud Tasks retry mechanism
        raise


async def run_gemini_analysis(
    media_asset_id: UUID, 
    background_tasks: BackgroundTasks | None = None,
    use_cloud_tasks: bool = True,
    chat_id: str | None = None,
    user_id: str | None = None,
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
        analysis_id, status, created_at, was_created = await claim_or_create_analysis(
            conn,
            media_asset_id=media_asset_id,
            prompt=DEFAULT_ANALYSIS_PROMPT,
        )
        
        # Determine if we should spawn a task
        should_spawn_task = was_created
        
        # If existing analysis is completed, return cached result
        if not was_created and status == "completed":
            existing = await get_video_analysis_by_media_asset(conn, media_asset_id)
            analysis_str = None
            if existing and existing.get("analysis_result"):
                analysis_data = existing["analysis_result"]
                analysis_str = analysis_data.get("analysis") if isinstance(analysis_data, dict) else None
            await conn.commit() # Commit before returning
            return VideoAnalysisResponse(
                id=analysis_id,
                media_asset_id=media_asset_id,
                status="completed",
                analysis=analysis_str,
                error=existing.get("error") if existing else None,
                created_at=existing["created_at"] if existing else datetime.utcnow(),
                cached=True,
            )
        
        # Check for STALE or FAILED tasks that need rescuing
        if not was_created:
            # Check if stuck in "queued" or "processing" for too long (e.g., 10 minutes)
            is_stale = False
            if status in ("queued", "processing") and created_at:
                # Ensure created_at is aware if possible, otherwise handle naive
                now = datetime.now(timezone.utc) if created_at.tzinfo else datetime.utcnow()
                time_diff = now - created_at
                if time_diff.total_seconds() > 600: # 10 minutes
                    is_stale = True
                    logger.warning(f"[ANALYSIS] Found stale analysis {analysis_id} (status={status}, age={time_diff.total_seconds()}s). Rescuing.")
            
            if status == "failed" or is_stale:
                # Force reset to 'queued' with new timestamp
                logger.info(f"[ANALYSIS] Rescuing {status} analysis {analysis_id}")
                await update_analysis_status(
                    conn,
                    analysis_id=analysis_id,
                    status="queued",
                    created_at=datetime.utcnow(),
                    error=None # Clear previous error
                )
                should_spawn_task = True
                status = "queued" # Update local status variable for response
        
        await conn.commit()
        
        # Return if running and healthy (not just rescued/created)
        if not should_spawn_task:
            return VideoAnalysisResponse(
                id=analysis_id,
                media_asset_id=media_asset_id,
                status=status,
                analysis=None,
                created_at=created_at,
                cached=True,
            )
        
        logger.info(f"Created/Rescued analysis {analysis_id} for media_asset {media_asset_id}")

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
                "attempt_no": 0,
            }
        )

    # 4. Spawn background task for LLM processing
    logger.info(f"[ANALYSIS] Spawning background task for analysis_id={analysis_id}")
    
    if use_cloud_tasks or not background_tasks:
        logger.info(f"[ANALYSIS] Using Cloud Tasks (queue={settings.QUEUE_GEMINI}) for analysis {analysis_id}")
        
        # Determine dispatched_at
        import time
        dispatched_at = time.time()
        
        await cloud_tasks.create_http_task(
            queue_name=settings.QUEUE_GEMINI,
            relative_uri="/v1/tasks/gemini/analyze",
            payload={
                "analysis_id": str(analysis_id),
                "media_asset_id": str(media_asset_id),
                "video_uri": video_uri,
                "chat_id": chat_id,
                "user_id": user_id,
                "dispatched_at": dispatched_at,
                "attempt_no": 0,
            }
        )
    else:
        # Legacy/Local mode (fallback)
        import asyncio
        asyncio.create_task(
            _execute_gemini_analysis(
                analysis_id=analysis_id,
                media_asset_id=media_asset_id,
                video_uri=video_uri,
                chat_id=chat_id,
                user_id=user_id,
            )
        )
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


async def run_gemini_analysis_batch(
    media_asset_ids: list[UUID],
    background_tasks: BackgroundTasks | None = None,
    use_cloud_tasks: bool = True,
    chat_id: str | None = None,
    user_id: str | None = None,
) -> list[VideoAnalysisResponse]:
    """
    Batch Gemini analysis dispatcher.
    - Claims/creates analysis rows in bulk
    - Rescues stale/failed rows in bulk
    - Dispatches one or more batched task payloads
    """
    deduped_ids = list(dict.fromkeys(media_asset_ids))
    if not deduped_ids:
        return []

    response_by_asset: dict[UUID, VideoAnalysisResponse] = {}
    to_spawn_payloads: list[dict[str, Any]] = []
    priority_download_asset_ids: list[UUID] = []

    async with get_db_connection() as conn:
        media_assets = await get_media_assets_by_ids(conn, deduped_ids)
        media_by_id = {row["id"]: row for row in media_assets}
        existing_asset_ids = [asset_id for asset_id in deduped_ids if asset_id in media_by_id]

        for missing_id in [asset_id for asset_id in deduped_ids if asset_id not in media_by_id]:
            response_by_asset[missing_id] = VideoAnalysisResponse(
                media_asset_id=missing_id,
                status="failed",
                analysis=None,
                error="Media asset not found",
                created_at=datetime.utcnow(),
                cached=False,
            )

        if existing_asset_ids:
            create_result = await claim_or_create_analyses_batch(
                conn,
                media_asset_ids=existing_asset_ids,
                prompt=DEFAULT_ANALYSIS_PROMPT,
            )
            was_created_map = {
                asset_id: bool(meta.get("was_created"))
                for asset_id, meta in create_result.items()
            }

            analyses = await get_video_analyses_by_media_assets(conn, existing_asset_ids)
            analysis_by_asset = {row["media_asset_id"]: row for row in analyses}
            rescued_ids = await rescue_stale_or_failed_analyses_batch(
                conn,
                [
                    {
                        "analysis_id": row["id"],
                        "status": row.get("status"),
                        "created_at": row.get("created_at"),
                    }
                    for row in analyses
                ],
            )

            for row in analyses:
                if row["id"] in rescued_ids:
                    row["status"] = "queued"
                    row["error"] = None
                    row["created_at"] = datetime.utcnow()

            for media_asset_id in existing_asset_ids:
                media_asset = media_by_id[media_asset_id]
                source_url = media_asset.get("source_url", "")
                is_youtube = "youtube.com" in source_url or "youtu.be" in source_url
                video_uri = source_url if is_youtube else (
                    media_asset.get("gcs_uri") or media_asset.get("video_url") or source_url
                )

                analysis_row = analysis_by_asset.get(media_asset_id)
                if not analysis_row:
                    response_by_asset[media_asset_id] = VideoAnalysisResponse(
                        media_asset_id=media_asset_id,
                        status="failed",
                        analysis=None,
                        error="Analysis row not found",
                        created_at=datetime.utcnow(),
                        cached=False,
                    )
                    continue

                if not video_uri:
                    response_by_asset[media_asset_id] = VideoAnalysisResponse(
                        id=analysis_row["id"],
                        media_asset_id=media_asset_id,
                        status="failed",
                        analysis=None,
                        error="No video URL available for analysis",
                        created_at=analysis_row.get("created_at"),
                        cached=False,
                    )
                    continue

                status = analysis_row.get("status", "queued")
                if status == "completed":
                    analysis_data = analysis_row.get("analysis_result") or {}
                    analysis_text = analysis_data.get("analysis") if isinstance(analysis_data, dict) else None
                    response_by_asset[media_asset_id] = VideoAnalysisResponse(
                        id=analysis_row["id"],
                        media_asset_id=media_asset_id,
                        status="completed",
                        analysis=analysis_text,
                        error=analysis_row.get("error"),
                        created_at=analysis_row.get("created_at"),
                        cached=True,
                    )
                    continue

                should_spawn = was_created_map.get(media_asset_id, False) or (analysis_row["id"] in rescued_ids)
                if not should_spawn:
                    response_by_asset[media_asset_id] = VideoAnalysisResponse(
                        id=analysis_row["id"],
                        media_asset_id=media_asset_id,
                        status=status,
                        analysis=None,
                        error=analysis_row.get("error"),
                        created_at=analysis_row.get("created_at"),
                        cached=True,
                    )
                    continue

                to_spawn_payloads.append(
                    {
                        "analysis_id": str(analysis_row["id"]),
                        "media_asset_id": str(media_asset_id),
                        "video_uri": video_uri,
                        "chat_id": chat_id,
                        "user_id": user_id,
                        "dispatched_at": datetime.utcnow().timestamp(),
                        "attempt_no": 0,
                    }
                )
                if not is_youtube and media_asset.get("status") == "pending":
                    priority_download_asset_ids.append(media_asset_id)

                response_by_asset[media_asset_id] = VideoAnalysisResponse(
                    id=analysis_row["id"],
                    media_asset_id=media_asset_id,
                    status="processing",
                    analysis=None,
                    created_at=datetime.utcnow(),
                    cached=False,
                )
        await conn.commit()

    if priority_download_asset_ids:
        async with get_db_connection() as conn:
            download_infos = await get_media_asset_download_info_by_ids(conn, priority_download_asset_ids)
            await conn.commit()
        if download_infos:
            batch_size = max(1, int(getattr(settings, "MEDIA_DOWNLOAD_ENQUEUE_BATCH_SIZE", 50)))
            payloads = [
                {
                    "asset_id": str(row["media_asset_id"]),
                    "platform": row.get("platform") or "unknown",
                    "external_id": row.get("external_id") or "unknown",
                    "priority": True,
                    "attempt_no": 0,
                }
                for row in download_infos
            ]
            for idx in range(0, len(payloads), batch_size):
                await cloud_tasks.create_http_task(
                    queue_name=settings.QUEUE_MEDIA_DOWNLOAD_PRIORITY,
                    relative_uri="/v1/tasks/media/download",
                    payload=payloads[idx: idx + batch_size],
                )

    if to_spawn_payloads:
        if use_cloud_tasks or not background_tasks:
            batch_size = max(1, int(getattr(settings, "GEMINI_TASK_ENQUEUE_BATCH_SIZE", 100)))
            for idx in range(0, len(to_spawn_payloads), batch_size):
                await cloud_tasks.create_http_task(
                    queue_name=settings.QUEUE_GEMINI,
                    relative_uri="/v1/tasks/gemini/analyze",
                    payload=to_spawn_payloads[idx: idx + batch_size],
                )
        else:
            for payload in to_spawn_payloads:
                asyncio.create_task(
                    _execute_gemini_analysis(
                        analysis_id=UUID(payload["analysis_id"]),
                        media_asset_id=UUID(payload["media_asset_id"]),
                        video_uri=payload["video_uri"],
                        chat_id=payload.get("chat_id"),
                        user_id=payload.get("user_id"),
                    )
                )

    return [response_by_asset[asset_id] for asset_id in deduped_ids if asset_id in response_by_asset]


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
    
    # if not is_youtube:
    #     # Trigger 12Labs Indexing in Background (only for non-YouTube)
    #     await cloud_tasks.create_http_task(
    #         queue_name=settings.QUEUE_TWELVELABS,
    #         relative_uri="/v1/tasks/twelvelabs/index",
    #         payload={"media_asset_id": str(media_asset_id)}
    #     )
    
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
        analysis_str = None
        if status == "completed" and existing.get("analysis_result"):
            analysis_data = existing["analysis_result"]
            analysis_str = analysis_data.get("analysis") if isinstance(analysis_data, dict) else None
        
        return VideoAnalysisResponse(
            id=existing["id"],
            media_asset_id=media_asset_id,
            status=status,
            analysis=analysis_str,
            error=existing.get("error"),
            created_at=existing["created_at"],
            cached=True,
        )
