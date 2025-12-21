
from uuid import UUID
import httpx

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core import get_settings, logger
from app.db.session import get_db_connection
from app.api.v1.analysis import _execute_gemini_analysis
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
    raw_json: dict

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
    """
    logger.info(f"Received raw archive task for search {payload.search_id} platform {payload.platform}")
    await upload_raw_json_gz(
        platform=payload.platform,
        search_id=payload.search_id,
        raw_json=payload.raw_json
    )
    return {"status": "ok"}
