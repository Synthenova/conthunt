import asyncio
import base64
import gzip
import json
from uuid import UUID
import httpx

from app.services.task_executor import CloudTaskExecutor
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.core import get_settings, logger
from app.db.session import get_db_connection
from app.api.v1.analysis import _execute_gemini_analysis
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
    logger.info(f"Received media download task for {payload.asset_id}")
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
    logger.info(f"Received raw archive task for search {payload.search_id} platform {payload.platform}")
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
    )
