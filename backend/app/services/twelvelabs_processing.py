"""Background processing for TwelveLabs video analysis."""
import logging
import asyncio
from uuid import UUID
from datetime import datetime

from app.core.settings import get_settings
from app.db.session import get_db_connection
from app.db.queries import (
    get_content_item_by_id,
    upsert_twelvelabs_asset,
    update_twelvelabs_asset_status,
    get_twelvelabs_asset_by_content_item
)
from app.services.twelvelabs_client import (
    get_twelvelabs_client,
)
from app.storage.gcs import gcs_client

logger = logging.getLogger(__name__)


async def _archive_twelvelabs_response(
    content_item_id: UUID,
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
    key = f"twelvelabs/{operation}/{now.year}/{now.month:02d}/{now.day:02d}/{content_item_id}.json.gz"
    
    try:
        uri = gcs_client.upload_json_gz(
            bucket_name=settings.GCS_BUCKET_RAW,
            key=key,
            data=raw_response,
        )
        logger.info(f"Archived TwelveLabs {operation} response for {content_item_id}")
        return uri
    except Exception as e:
        logger.error(f"Failed to archive TwelveLabs response: {e}")
        return None


async def process_twelvelabs_indexing(content_item_id: UUID):
    """
    Background task to handle TwelveLabs indexing flow (Upload -> Index).
    
    1. Upload video (if needed)
    2. Index video (if needed)
    
    Handles DB updates and error status setting.
    """
    logger.info(f"Starting background indexing for content item {content_item_id}")
    settings = get_settings()
    
    try:
        async with get_db_connection() as conn:
            # 1. Get content item and video URL
            content_item = await get_content_item_by_id(conn, content_item_id)
            if not content_item:
                logger.error(f"Content item {content_item_id} not found")
                return
            
            video_url = content_item.get("video_url")
            if not video_url:
                logger.error(f"No video URL for content item {content_item_id}")
                return
            

            # 2. Concurrency Check & Initialization
            # Check if we are already processing this item
            existing_asset = await get_twelvelabs_asset_by_content_item(conn, content_item_id)
            if existing_asset:
                status = existing_asset.get("asset_status")
                idx_status = existing_asset.get("index_status")
                
                # If currently working, abort
                if status in ("uploading", "processing") or idx_status in ("queued", "indexing", "processing"):
                    logger.info(f"Indexing already in progress for {content_item_id} (status: {status}/{idx_status}), skipping")
                    return
                
                # If both ready, nothing to do
                if status == "ready" and idx_status == "ready":
                     logger.info(f"Asset already fully indexed for {content_item_id}, skipping")
                     return
            
            # 3. Initialize TwelveLabs client
            try:
                client = get_twelvelabs_client()
            except ValueError as e:
                logger.error(f"TwelveLabs client init failed: {e}")
                return
            
            # Using static index ID from settings
            tl_index_id = settings.TWELVELABS_INDEX_ID
            if not tl_index_id:
                logger.error("TWELVELABS_INDEX_ID is not configured")
                return

            # Determine where to start
            current_asset_id = None
            current_indexed_asset_id = None
            
            if existing_asset:
                 current_asset_id = existing_asset.get("asset_id")
                 # Check if we have a valid index ID match
                 if existing_asset.get("index_id") != tl_index_id:
                      logger.warning(f"Existing asset index ID mismatch for {content_item_id}, might re-upload/index")
                      # Ideally we handle this, but for now proceed with existing asset if ID present

                 if existing_asset.get("index_status") == "ready":
                      current_indexed_asset_id = existing_asset.get("indexed_asset_id")
            
            if current_asset_id and existing_asset.get("asset_status") == "ready":
                 logger.info(f"Asset already uploaded: {current_asset_id}")

            # 4. Upload Step
            if not current_asset_id or existing_asset.get("asset_status") != "ready":
                if not current_asset_id:
                     logger.info(f"Starting upload for {content_item_id}...")
                     
                     # Pre-insert to lock and track
                     await upsert_twelvelabs_asset(
                         conn,
                         content_item_id=content_item_id,
                         index_id=tl_index_id,
                         asset_id="pending", # Temporary
                         asset_status="uploading"
                     )
                     await conn.commit()

                try:
                    # If we don't have asset ID, upload.
                    # If we have one but status failed, retrying upload might create new asset ID
                    asset_id, upload_raw = await client.upload_asset(video_url)
                    
                    upload_gcs_uri = await _archive_twelvelabs_response(
                        content_item_id, "upload", upload_raw
                    )
                    
                    # Update with real ID
                    await upsert_twelvelabs_asset(
                        conn,
                        content_item_id=content_item_id,
                        index_id=tl_index_id,
                        asset_id=asset_id,
                        asset_status="processing",
                        upload_raw_gcs_uri=upload_gcs_uri,
                    )
                    await conn.commit()
                    current_asset_id = asset_id
                    
                except Exception as e:
                    logger.error(f"Upload failed: {e}")
                    await update_twelvelabs_asset_status(
                        conn, content_item_id, asset_status="failed", error=f"Upload error: {str(e)}"
                    )
                    await conn.commit()
                    return

                # Wait for upload readiness
                upload_ready = await client.wait_for_asset_ready(current_asset_id)
                if not upload_ready:
                    await update_twelvelabs_asset_status(
                        conn, content_item_id, asset_status="failed", error="Upload timeout"
                    )
                    await conn.commit()
                    return
                
                await update_twelvelabs_asset_status(
                    conn, content_item_id, asset_status="ready"
                )
                await conn.commit()

            # 5. Index Step
            if not current_indexed_asset_id:
                logger.info(f"Indexing asset {current_asset_id}...")
                
                # Mark as indexing
                await update_twelvelabs_asset_status(
                    conn, content_item_id, index_status="queued"
                )
                await conn.commit()

                try:
                    indexed_asset_id, index_raw = await client.index_asset(tl_index_id, current_asset_id)
                    index_gcs_uri = await _archive_twelvelabs_response(
                        content_item_id, "index", index_raw
                    )
                    
                    await update_twelvelabs_asset_status(
                        conn,
                        content_item_id,
                        indexed_asset_id=indexed_asset_id,
                        index_status="processing", # indexing
                        index_raw_gcs_uri=index_gcs_uri,
                    )
                    await conn.commit()
                    current_indexed_asset_id = indexed_asset_id
                    
                except Exception as e:
                    logger.error(f"Indexing request failed: {e}")
                    await update_twelvelabs_asset_status(
                        conn, content_item_id, index_status="failed", error=f"Indexing error: {str(e)}"
                    )
                    await conn.commit()
                    return

                # Wait for indexing readiness
                index_ready = await client.wait_for_indexing_ready(
                    tl_index_id, current_indexed_asset_id
                )
                if not index_ready:
                    await update_twelvelabs_asset_status(
                        conn, content_item_id, index_status="failed", error="Indexing timeout"
                    )
                    await conn.commit()
                    return
                
                await update_twelvelabs_asset_status(
                    conn, content_item_id, index_status="ready"
                )
                await conn.commit()
            
            logger.info(f"Background indexing complete for {content_item_id}")

                
    except Exception as e:
        logger.error(f"Fatal error in background task: {e}", exc_info=True)
