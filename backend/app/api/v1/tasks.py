import base64
import gzip
import json
from uuid import UUID
import httpx

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core import get_settings, logger
from app.db.session import get_db_connection
from app.api.v1.analysis import _execute_gemini_analysis
from app.services.board_insights import execute_board_insights
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
from app.media.downloader import download_asset_with_claim
from app.storage.raw_archive import upload_raw_json_gz

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
async def handle_gemini_analysis_task(payload: AnalysisTaskPayload):
    """
    Handle background Gemini analysis task.
    """
    logger.info(f"Received Gemini analysis task for {payload.media_asset_id}")
    await _execute_gemini_analysis(
        analysis_id=payload.analysis_id,
        media_asset_id=payload.media_asset_id,
        video_uri=payload.video_uri
    )
    return {"status": "ok"}

@router.post("/twelvelabs/index")
async def handle_twelvelabs_index_task(payload: TwelveLabsTaskPayload):
    """
    Handle background TwelveLabs indexing task.
    """
    logger.info(f"Received TwelveLabs indexing task for {payload.media_asset_id}")
    await process_twelvelabs_indexing_by_media_asset(payload.media_asset_id)
    return {"status": "ok"}

@router.post("/media/download")
async def handle_media_download_task(payload: MediaDownloadTaskPayload):
    """
    Handle background media download task (one asset).
    """
    logger.info(f"Received media download task for {payload.asset_id}")
    async with httpx.AsyncClient(timeout=settings.MEDIA_HTTP_TIMEOUT_S, follow_redirects=True) as client:
        await download_asset_with_claim(
            http_client=client,
            asset_id=payload.asset_id,
            platform=payload.platform,
            external_id=payload.external_id
        )
    return {"status": "ok"}

@router.post("/raw/archive")
async def handle_raw_archive_task(payload: RawArchiveTaskPayload):
    """
    Handle background raw archive task.
    Uploads already-compressed data directly to GCS.
    """
    from app.storage.raw_archive import upload_raw_compressed
    
    logger.info(f"Received raw archive task for search {payload.search_id} platform {payload.platform}")
    
    # Decode base64 to get compressed bytes (already gzipped)
    compressed_bytes = base64.b64decode(payload.raw_json_compressed)
    
    await upload_raw_compressed(
        platform=payload.platform,
        search_id=payload.search_id,
        compressed_data=compressed_bytes
    )
    return {"status": "ok"}

@router.post("/boards/insights")
async def handle_board_insights_task(payload: BoardInsightsTaskPayload):
    """
    Handle background board insights task.
    """
    logger.info(f"Received board insights task for board {payload.board_id}")
    await execute_board_insights(
        board_id=payload.board_id,
        user_id=payload.user_id,
    )
    return {"status": "ok"}
