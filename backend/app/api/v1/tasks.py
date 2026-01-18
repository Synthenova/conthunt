import asyncio
import base64
import gzip
import json
from uuid import UUID
import httpx

from app.services.task_executor import CloudTaskExecutor
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import redis.asyncio as redis

from app.core import get_settings, logger
from app.db.session import get_db_connection
from app.api.v1.analysis import _execute_gemini_analysis
from app.api.v1.search import search_worker, load_more_worker
from app.api.v1.chats import stream_generator_to_redis
from app.agent.runtime import create_agent_graph
from app.services.board_insights import execute_board_insights
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
from app.media.downloader import download_asset_with_claim, update_asset_failed
from app.db.queries.analysis import update_analysis_status
from app.db.queries import update_twelvelabs_asset_status, update_board_insights_status
from app.db.queries.content import get_media_asset_by_id

router = APIRouter()
settings = get_settings()

class AnalysisTaskPayload(BaseModel):
    analysis_id: UUID
    media_asset_id: UUID
    video_uri: str

class TwelveLabsTaskPayload(BaseModel):
    media_asset_id: UUID

class MediaDownloadTaskPayload(BaseModel):
    asset_id: UUID
    platform: str
    external_id: str

class RawArchiveTaskPayload(BaseModel):
    platform: str
    search_id: UUID
    raw_json_compressed: str  # base64-encoded gzip data

class BoardInsightsTaskPayload(BaseModel):
    board_id: UUID
    user_id: UUID
    user_role: str

class SearchTaskPayload(BaseModel):
    search_id: UUID
    user_uuid: UUID
    query: str
    inputs: dict

class LoadMoreTaskPayload(BaseModel):
    search_id: UUID
    user_uuid: UUID
    query: str
    platform_cursors: dict

class ChatStreamTaskPayload(BaseModel):
    chat_id: UUID
    thread_id: str
    inputs: dict
    model_name: str | None = None
    image_urls: list[str] | None = None
    auth_token: str | None = None

@router.post("/gemini/analyze")
async def handle_gemini_analysis_task(payload: AnalysisTaskPayload, request: Request):
    """
    Handle background Gemini analysis task with retries.
    Waits inline for video to be ready (max 3 min), then analyzes.
    """
    logger.info(f"Received Gemini analysis task for {payload.media_asset_id}")
    executor = CloudTaskExecutor(request)

    async def _on_fail(e: Exception):
        async with get_db_connection() as conn:
            await update_analysis_status(
                conn,
                analysis_id=payload.analysis_id,
                status="failed",
                error=str(e),
            )
            await conn.commit()

    # Mark as processing on pickup
    async with get_db_connection() as conn:
        await update_analysis_status(conn, payload.analysis_id, status="processing")
        await conn.commit()

    # Get asset info
    async with get_db_connection() as conn:
        asset = await get_media_asset_by_id(conn, payload.media_asset_id)
    
    if not asset:
        await _on_fail(Exception("Media asset not found"))
        return {"status": "failed", "error": "Media asset not found"}
    
    source_url = asset.get("source_url", "")
    is_youtube = "youtube.com" in source_url or "youtu.be" in source_url
    
    # YouTube doesn't need GCS upload, others need to wait for download
    if not is_youtube:
        # Poll until video ready or timeout (max 3 min)
        for attempt in range(18):  # 18 x 10s = 3 min
            async with get_db_connection() as conn:
                asset = await get_media_asset_by_id(conn, payload.media_asset_id)
            
            status = asset.get("status", "") if asset else ""
            if status in ("stored", "downloaded"):
                logger.info(f"Video ready (status={status}) for {payload.media_asset_id}")
                break
            if status == "failed":
                await _on_fail(Exception("Video download failed"))
                return {"status": "failed", "error": "Video download failed"}
            
            logger.info(f"Video not ready (status={status}), waiting... attempt {attempt+1}/18 for {payload.media_asset_id}")
            await asyncio.sleep(10)
        else:
            await _on_fail(Exception("Video not ready after 3 min timeout"))
            return {"status": "failed", "error": "Video not ready after timeout"}

    # Use fresh video URI from asset if available (e.g. GCS URI after download)
    final_video_uri = payload.video_uri
    if asset:
        final_video_uri = asset.get("gcs_uri") or asset.get("video_url") or payload.video_uri

    return await executor.run(
        handler=_execute_gemini_analysis,
        on_fail=_on_fail,
        analysis_id=payload.analysis_id,
        media_asset_id=payload.media_asset_id,
        video_uri=final_video_uri
    )

@router.post("/twelvelabs/index")
async def handle_twelvelabs_index_task(payload: TwelveLabsTaskPayload, request: Request):
    """
    Handle background TwelveLabs indexing task with retries.
    Waits inline for video to be ready (max 3 min), then indexes.
    """
    logger.info(f"Received TwelveLabs indexing task for {payload.media_asset_id}")
    executor = CloudTaskExecutor(request)

    async def _on_fail(e: Exception):
        async with get_db_connection() as conn:
            # Mark both statuses as failed ensures we catch the error regardless of phase
            await update_twelvelabs_asset_status(
                conn, 
                media_asset_id=payload.media_asset_id, 
                asset_status="failed",
                index_status="failed", 
                error=str(e)
            )
            await conn.commit()

    # Mark as processing on pickup
    async with get_db_connection() as conn:
        await update_twelvelabs_asset_status(
            conn, 
            media_asset_id=payload.media_asset_id, 
            asset_status="processing",
            index_status="processing", 
        )
        await conn.commit()

    # Get asset info
    async with get_db_connection() as conn:
        asset = await get_media_asset_by_id(conn, payload.media_asset_id)
    
    if not asset:
        await _on_fail(Exception("Media asset not found"))
        return {"status": "failed", "error": "Media asset not found"}
    
    # Poll until video ready or timeout (max 3 min)
    for attempt in range(18):  # 18 x 10s = 3 min
        async with get_db_connection() as conn:
            asset = await get_media_asset_by_id(conn, payload.media_asset_id)
        
        status = asset.get("status", "") if asset else ""
        if status in ("stored", "downloaded"):
            logger.info(f"Video ready (status={status}) for TwelveLabs {payload.media_asset_id}")
            break
        if status == "failed":
            await _on_fail(Exception("Video download failed"))
            return {"status": "failed", "error": "Video download failed"}
        
        logger.info(f"Video not ready (status={status}), waiting... attempt {attempt+1}/18 for TwelveLabs {payload.media_asset_id}")
        await asyncio.sleep(10)
    else:
        await _on_fail(Exception("Video not ready after 3 min timeout"))
        return {"status": "failed", "error": "Video not ready after timeout"}

    return await executor.run(
        handler=process_twelvelabs_indexing_by_media_asset,
        on_fail=_on_fail,
        media_asset_id=payload.media_asset_id
    )

@router.post("/media/download")
async def handle_media_download_task(payload: MediaDownloadTaskPayload, request: Request):
    """
    Handle background media download task (one asset) with retries.
    """
    logger.debug(f"Received media download task for {payload.asset_id}")
    executor = CloudTaskExecutor(request)

    async def _on_fail(e: Exception):
        async with get_db_connection() as conn:
            await update_asset_failed(conn, payload.asset_id, str(e))

    async with httpx.AsyncClient(timeout=settings.MEDIA_HTTP_TIMEOUT_S, follow_redirects=True) as client:
        return await executor.run(
            handler=download_asset_with_claim,
            on_fail=_on_fail,
            http_client=client,
            asset_id=payload.asset_id,
            platform=payload.platform,
            external_id=payload.external_id
        )

@router.post("/raw/archive")
async def handle_raw_archive_task(payload: RawArchiveTaskPayload, request: Request):
    """
    Handle background raw archive task with retries.
    """
    from app.storage.raw_archive import upload_raw_compressed
    logger.debug(f"Received raw archive task for search {payload.search_id} platform {payload.platform}")
    executor = CloudTaskExecutor(request)
    
    # Decode base64 to get compressed bytes (already gzipped)
    compressed_bytes = base64.b64decode(payload.raw_json_compressed)

    async def _on_fail(e: Exception):
        logger.error(f"Raw archive permanently failed for search {payload.search_id}")

    return await executor.run(
        handler=upload_raw_compressed,
        on_fail=_on_fail,
        platform=payload.platform,
        search_id=payload.search_id,
        compressed_data=compressed_bytes
    )

@router.post("/boards/insights")
async def handle_board_insights_task(payload: BoardInsightsTaskPayload, request: Request):
    """
    Handle background board insights task with retries.
    Marks status='processing' on pickup.
    """
    from app.db.queries import get_board_insights
    from app.db import set_rls_user
    
    logger.info(f"Received board insights task for board {payload.board_id}")
    executor = CloudTaskExecutor(request)

    async def _on_fail(e: Exception):
        async with get_db_connection() as conn:
            await set_rls_user(conn, payload.user_id)
            row = await get_board_insights(conn, payload.board_id)
            if row:
                await update_board_insights_status(
                    conn,
                    insights_id=row["id"],
                    status="failed",
                    error=str(e),
                )
                await conn.commit()

    # Mark as processing on pickup
    async with get_db_connection() as conn:
        await set_rls_user(conn, payload.user_id)
        row = await get_board_insights(conn, payload.board_id)
        if row and row.get("status") == "queued":
            await update_board_insights_status(
                conn,
                insights_id=row["id"],
                status="processing",
            )
            await conn.commit()

    return await executor.run(
        handler=execute_board_insights,
        on_fail=_on_fail,
        board_id=payload.board_id,
        user_id=payload.user_id,
        user_role=payload.user_role,
    )

@router.post("/search/run")
async def handle_search_task(payload: SearchTaskPayload, request: Request):
    """
    Handle background search task with retries.
    """
    logger.info(f"Received search task for {payload.search_id}")
    executor = CloudTaskExecutor(request)

    async def _on_fail(e: Exception):
        logger.error(f"Search task permanently failed for {payload.search_id}: {e}")

    return await executor.run(
        handler=search_worker,
        on_fail=_on_fail,
        search_id=payload.search_id,
        user_uuid=payload.user_uuid,
        query=payload.query,
        inputs=payload.inputs,
    )

@router.post("/search/load_more")
async def handle_load_more_task(payload: LoadMoreTaskPayload, request: Request):
    """
    Handle background load-more task with retries.
    """
    logger.info(f"Received load_more task for {payload.search_id}")
    executor = CloudTaskExecutor(request)

    async def _on_fail(e: Exception):
        logger.error(f"Load more task permanently failed for {payload.search_id}: {e}")

    return await executor.run(
        handler=load_more_worker,
        on_fail=_on_fail,
        search_id=payload.search_id,
        user_uuid=payload.user_uuid,
        query=payload.query,
        platform_cursors=payload.platform_cursors,
    )

@router.post("/chats/stream")
async def handle_chat_stream_task(payload: ChatStreamTaskPayload, request: Request):
    """
    Handle background chat stream task with retries.
    """
    logger.info(f"Received chat stream task for {payload.chat_id}")
    executor = CloudTaskExecutor(request)

    async def _on_fail(e: Exception):
        logger.error(f"Chat stream task permanently failed for {payload.chat_id}: {e}")
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            await r.xadd(
                f"chat:{str(payload.chat_id)}:stream",
                {"data": json.dumps({"type": "error", "error": str(e)})},
            )
            await r.expire(f"chat:{str(payload.chat_id)}:stream", 60)
        finally:
            await r.close()

    async def _run_chat_stream():
        graph, saver_cm = await create_agent_graph(settings.DATABASE_URL)
        try:
            await stream_generator_to_redis(
                graph=graph,
                chat_id=str(payload.chat_id),
                thread_id=payload.thread_id,
                inputs=payload.inputs,
                context={"x-auth-token": payload.auth_token} if payload.auth_token else None,
                model_name=payload.model_name,
                image_urls=payload.image_urls or [],
            )
        finally:
            try:
                await saver_cm.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Failed to close chat saver context: {e}")

    return await executor.run(
        handler=_run_chat_stream,
        on_fail=_on_fail,
    )
