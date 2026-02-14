import logging
import asyncio
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Header
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import text

from app.core import logger
from app.auth.firebase import get_current_user
from app.db.session import get_db_connection
from app.db import set_rls_user
from app.agent.model_factory import init_chat_model
from app.db.queries.analysis import (
    get_video_analysis_by_media_asset,
    update_analysis_status,
)
from app.db.queries.content import get_media_asset_by_id
from app.schemas.analysis import VideoAnalysisResponse
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
from app.services.cloud_tasks import cloud_tasks
from app.core import get_settings
from app.prompts.video_analysis import DEFAULT_ANALYSIS_PROMPT
from app.core.redis_client import get_global_redis
from app.realtime.stream_hub import stream_id_gt
from app.llm.context import set_llm_context

settings = get_settings()

load_dotenv()

router = APIRouter(tags=["video-analysis"])

import json


def _is_terminal_payload(payload_str: str | None) -> bool:
    if not payload_str:
        return False
    return ('"type": "done"' in payload_str) or ('"type": "error"' in payload_str)

# Initialize Gemini Model
llm = init_chat_model("google/gemini-2.5-flash-lite-preview-09-2025", temperature=0.7)



async def _publish_analysis_event(
    chat_id: str | None,
    analysis_id: UUID,
    media_asset_id: UUID,
    status: str,
    error: str | None = None,
) -> None:
    if not chat_id:
        return
    payload = {
        "type": "analysis",
        "analysis_id": str(analysis_id),
        "media_asset_id": str(media_asset_id),
        "status": status,
    }
    if error:
        payload["error"] = error
    try:
        redis_client = get_global_redis()
        stream_key = f"analysis:{chat_id}:stream"
        await redis_client.xadd(
            stream_key,
            {"data": json.dumps(payload)},
            maxlen=settings.REDIS_STREAM_MAXLEN_SEARCH,
            approximate=True,
        )
        await redis_client.expire(stream_key, settings.REDIS_STREAM_TTL_S_SEARCH)
    except Exception as exc:
        logger.warning("[ANALYSIS] Failed to publish analysis event: %s", exc)


async def _execute_gemini_analysis(
    analysis_id: UUID,
    media_asset_id: UUID,
    video_uri: str,
    chat_id: str | None = None,
    user_id: str | None = None,
) -> None:
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
    
    try:
        # 1. Build Message with prompt
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
        
        # 2. Invoke LLM (plain text output - markdown)
        logger.info(f"[ANALYSIS] Invoking Gemini LLM (markdown output)...")
        invoke_start = time.time()

        with set_llm_context(user_id=user_id, route="analysis.video"):
            response = await llm.ainvoke([message], **{"max_output_tokens": 4096})
        
        analysis_markdown = response.content
        invoke_duration = time.time() - invoke_start
        
        logger.info(f"[ANALYSIS] Gemini LLM returned in {invoke_duration:.2f}s")
        logger.info(f"[ANALYSIS] Result preview: {analysis_markdown[:200]}...")
        
        # 3. Update to completed - save as {"analysis": markdown_string}
        logger.info(f"[ANALYSIS] Updating status to 'completed'...")
        async with get_db_connection() as conn:
            await update_analysis_status(
                conn,
                analysis_id=analysis_id,
                status="completed",
                analysis_result={"analysis": analysis_markdown},
            )
            await conn.commit()
        await _publish_analysis_event(
            chat_id=chat_id,
            analysis_id=analysis_id,
            media_asset_id=media_asset_id,
            status="completed",
        )
        
        total_duration = time.time() - start_time
        logger.info(f"[ANALYSIS] ✅ Completed analysis for media_asset {media_asset_id} in {total_duration:.2f}s total")
    
    except Exception as e:
        # Mark as failed so insights don't get stuck waiting
        logger.error(f"[ANALYSIS] ❌ Failed analysis for media_asset {media_asset_id} (URL: {video_uri}): {e}")
        logger.error(traceback.format_exc())
        try:
            async with get_db_connection() as conn:
                await update_analysis_status(
                    conn,
                    analysis_id=analysis_id,
                    status="failed",
                    error=f"{e} (URL: {video_uri})",
                )
                await conn.commit()
            await _publish_analysis_event(
                chat_id=chat_id,
                analysis_id=analysis_id,
                media_asset_id=media_asset_id,
                status="failed",
                error=str(e),
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
                "video_uri": video_uri,
                "chat_id": chat_id,
                "user_id": user_id,
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


@router.get("/analysis/{chat_id}/stream")
async def stream_analysis(
    chat_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
    last_event_id: str | None = Header(None, alias="Last-Event-ID"),
):
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user token")

    # Verify user owns this chat
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        res = await conn.execute(
            text(
                """
                SELECT 1
                FROM conthunt.chats
                WHERE id = :chat_id AND deleted_at IS NULL
                """
            ),
            {"chat_id": chat_id},
        )
        if not res.fetchone():
            raise HTTPException(status_code=404, detail="Chat not found")

    stream_key = f"analysis:{chat_id}:stream"
    hub = getattr(request.app.state, "stream_hub", None)
    # Use the app-scoped Redis client if available; it shares the same pool as the hub.
    redis_client = getattr(request.app.state, "redis", None) or get_global_redis()

    async def event_generator():
        async def catch_up_from_redis(last_id: str):
            nonlocal last_sent_id
            cur = last_id or "0-0"
            while True:
                try:
                    streams = await redis_client.xread({stream_key: cur}, count=200, block=0)
                except Exception as exc:
                    # Most common cause: provider/proxy closes idle pooled sockets.
                    # Let the loop continue; the next command should acquire a fresh connection.
                    logger.warning("[ANALYSIS] Redis XREAD failed (catch-up): %s", exc)
                    await asyncio.sleep(0.2)
                    return
                if not streams:
                    return
                _, messages = streams[0]
                if not messages:
                    return
                for msg_id, data_map in messages:
                    payload_str = data_map.get("data")
                    cur = msg_id
                    last_sent_id = msg_id
                    if payload_str is None:
                        continue
                    yield {
                        "id": msg_id,
                        "event": "message",
                        "data": payload_str,
                    }
                    await asyncio.sleep(0)
                    if _is_terminal_payload(payload_str):
                        return
                if len(messages) < 200:
                    return

        if hub is None:
            last_id = last_event_id or "0-0"
            try:
                while True:
                    if await request.is_disconnected():
                        return
                    try:
                        streams = await redis_client.xread(
                            {stream_key: last_id},
                            count=50,
                            block=10000,
                        )
                    except Exception as exc:
                        logger.warning("[ANALYSIS] Redis XREAD failed (live): %s", exc)
                        await asyncio.sleep(0.2)
                        continue
                    if not streams:
                        yield {"event": "ping", "data": ""}
                        continue
                    for _, messages in streams:
                        for msg_id, data_map in messages:
                            last_id = msg_id
                            payload_str = data_map.get("data")
                            yield {
                                "id": msg_id,
                                "event": "message",
                                "data": payload_str,
                            }
                            await asyncio.sleep(0)
                            if _is_terminal_payload(payload_str):
                                return
            except asyncio.CancelledError:
                pass
            return

        queue = await hub.subscribe(stream_key)
        last_sent_id = last_event_id or "0-0"
        try:
            async for ev in catch_up_from_redis(last_sent_id):
                yield ev
                if _is_terminal_payload(ev.get("data")):
                    return

            while True:
                try:
                    msg_id, payload_str = await asyncio.wait_for(queue.get(), timeout=10)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
                    async for ev in catch_up_from_redis(last_sent_id):
                        yield ev
                        if _is_terminal_payload(ev.get("data")):
                            return
                    continue
                if not payload_str:
                    continue
                if not stream_id_gt(msg_id, last_sent_id):
                    continue
                last_sent_id = msg_id
                yield {
                    "id": msg_id,
                    "event": "message",
                    "data": payload_str,
                }
                await asyncio.sleep(0)
                if _is_terminal_payload(payload_str):
                    return
        except asyncio.CancelledError:
            pass
        finally:
            await hub.unsubscribe(stream_key, queue)

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return EventSourceResponse(event_generator(), headers=headers)
