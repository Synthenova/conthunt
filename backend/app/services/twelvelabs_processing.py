"""Background processing for TwelveLabs video analysis."""
import logging
import asyncio
from uuid import UUID
from datetime import datetime

from app.core.settings import get_settings
from app.db.session import get_db_connection
from app.db.queries import (
    get_video_media_asset_for_content_item,
    upsert_twelvelabs_asset,
    update_twelvelabs_asset_status,
    get_twelvelabs_asset_by_media_asset,
)
from app.services.twelvelabs_client import (
    get_twelvelabs_client,
)
from app.storage.gcs_async import async_gcs_client

logger = logging.getLogger(__name__)


async def _archive_twelvelabs_response(
    media_asset_id: UUID,
    operation: str,
    raw_response: dict,
) -> str | None:
    """
    Archive a TwelveLabs API response to GCS.
    
    Returns the gs:// URI or None if archiving is disabled/fails.
    """
    settings = get_settings()
    
    if not settings.RAW_UPLOAD_ENABLED:
        return None
    
    now = datetime.utcnow()
    key = f"twelvelabs/{operation}/{now.year}/{now.month:02d}/{now.day:02d}/{media_asset_id}.json.gz"
    
    try:
        uri = await async_gcs_client.upload_json_gz(
            bucket_name=settings.GCS_BUCKET_RAW,
            key=key,
            data=raw_response,
        )
        logger.info(f"Archived TwelveLabs {operation} response for media_asset {media_asset_id}")
        return uri
    except Exception as e:
        logger.error(f"Failed to archive TwelveLabs response: {e}")
        return None


async def process_twelvelabs_indexing_by_media_asset(media_asset_id: UUID):
    """
    Background task to handle TwelveLabs indexing flow (Upload -> Index).
    Takes media_asset_id directly (no resolution needed).
    """
    from app.db.queries.content import get_media_asset_by_id
    
    logger.info(f"Starting background indexing for media_asset {media_asset_id}")
    settings = get_settings()
    
    try:
        async with get_db_connection() as conn:
            # 1. Get media asset details
            media_asset = await get_media_asset_by_id(conn, media_asset_id)
            if not media_asset:
                logger.error(f"Media asset {media_asset_id} not found")
                return
            
            video_url = media_asset.get("video_url")
            if not video_url:
                logger.error(f"No video URL for media asset {media_asset_id}")
                return
            
            # 2. Check existing state
            existing_asset = await get_twelvelabs_asset_by_media_asset(conn, media_asset_id)
            if existing_asset:
                status = existing_asset.get("asset_status")
                idx_status = existing_asset.get("index_status")
                
                if status in ("uploading", "processing") or idx_status in ("queued", "indexing", "processing"):
                    logger.info(f"Indexing already in progress for media_asset {media_asset_id}, skipping")
                    return
                
                if status == "ready" and idx_status == "ready":
                    logger.info(f"Asset already fully indexed for media_asset {media_asset_id}, skipping")
                    return
            
            # 3. Initialize client
            try:
                client = get_twelvelabs_client()
            except ValueError as e:
                logger.error(f"TwelveLabs client init failed: {e}")
                return
            
            tl_index_id = settings.TWELVELABS_INDEX_ID
            if not tl_index_id:
                logger.error("TWELVELABS_INDEX_ID is not configured")
                return

            # Continue with upload/index logic (same as process_twelvelabs_indexing)
            current_asset_id = existing_asset.get("asset_id") if existing_asset else None
            current_indexed_asset_id = None
            
            if existing_asset and existing_asset.get("index_status") == "ready":
                current_indexed_asset_id = existing_asset.get("indexed_asset_id")
            
            # 4. Upload if needed
            if not current_asset_id or (existing_asset and existing_asset.get("asset_status") != "ready"):
                logger.info(f"Starting upload for media_asset {media_asset_id}...")
                
                await upsert_twelvelabs_asset(
                    conn, media_asset_id=media_asset_id, index_id=tl_index_id,
                    asset_id="pending", asset_status="uploading"
                )
                await conn.commit()

                try:
                    asset_id, upload_raw = await client.upload_asset(video_url)
                    upload_gcs_uri = await _archive_twelvelabs_response(media_asset_id, "upload", upload_raw)
                    
                    await upsert_twelvelabs_asset(
                        conn, media_asset_id=media_asset_id, index_id=tl_index_id,
                        asset_id=asset_id, asset_status="processing", upload_raw_gcs_uri=upload_gcs_uri
                    )
                    await conn.commit()
                    current_asset_id = asset_id
                except Exception as e:
                    logger.error(f"Upload failed: {e}")
                    await update_twelvelabs_asset_status(conn, media_asset_id, asset_status="failed", error=str(e))
                    await conn.commit()
                    return

                upload_ready = await client.wait_for_asset_ready(current_asset_id)
                if not upload_ready:
                    await update_twelvelabs_asset_status(conn, media_asset_id, asset_status="failed", error="Upload timeout")
                    await conn.commit()
                    return
                
                await update_twelvelabs_asset_status(conn, media_asset_id, asset_status="ready")
                await conn.commit()

            # 5. Index if needed
            if not current_indexed_asset_id:
                logger.info(f"Indexing asset {current_asset_id}...")
                await update_twelvelabs_asset_status(conn, media_asset_id, index_status="queued")
                await conn.commit()

                try:
                    indexed_asset_id, index_raw = await client.index_asset(tl_index_id, current_asset_id)
                    index_gcs_uri = await _archive_twelvelabs_response(media_asset_id, "index", index_raw)
                    
                    await update_twelvelabs_asset_status(
                        conn, media_asset_id, indexed_asset_id=indexed_asset_id,
                        index_status="processing", index_raw_gcs_uri=index_gcs_uri
                    )
                    await conn.commit()
                    current_indexed_asset_id = indexed_asset_id
                except Exception as e:
                    logger.error(f"Indexing failed: {e}")
                    await update_twelvelabs_asset_status(conn, media_asset_id, index_status="failed", error=str(e))
                    await conn.commit()
                    return

                index_ready = await client.wait_for_indexing_ready(tl_index_id, current_indexed_asset_id)
                if not index_ready:
                    await update_twelvelabs_asset_status(conn, media_asset_id, index_status="failed", error="Indexing timeout")
                    await conn.commit()
                    return
                
                await update_twelvelabs_asset_status(conn, media_asset_id, index_status="ready")
                await conn.commit()
            
            logger.info(f"Background indexing complete for media_asset {media_asset_id}")
                
    except Exception as e:
        logger.error(f"Fatal error in background task: {e}", exc_info=True)
