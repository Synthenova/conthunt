"""Raw API response archival to GCS."""
from datetime import datetime
from uuid import UUID
from typing import Optional

from app.core import get_settings, logger
from app.storage.gcs_async import async_gcs_client


async def upload_raw_json_gz(
    platform: str,
    search_id: UUID,
    raw_json: dict,
    key_override: str | None = None,
) -> Optional[str]:
    """
    Upload raw API response as gzipped JSON to GCS.
    
    Key format: raw/{platform}/{YYYY}/{MM}/{DD}/{search_id}.json.gz
    
    Returns the gs:// URI or None if RAW_UPLOAD_ENABLED=false.
    """
    settings = get_settings()
    
    if not settings.RAW_UPLOAD_ENABLED:
        logger.debug(f"Raw upload disabled, skipping for search {search_id}")
        return None
    
    if key_override:
        key = key_override
    else:
        now = datetime.utcnow()
        key = f"raw/{platform}/{now.year}/{now.month:02d}/{now.day:02d}/{search_id}.json.gz"
    
    try:
        uri = await async_gcs_client.upload_json_gz(
            bucket_name=settings.GCS_BUCKET_RAW,
            key=key,
            data=raw_json,
        )
        logger.info(f"Archived raw response for {platform} search {search_id}")
        return uri
    except Exception as e:
        logger.error(f"Failed to upload raw response: {e}")
        # Don't fail the request if archival fails
        return None


async def upload_raw_compressed(
    platform: str,
    search_id: UUID,
    compressed_data: bytes,
    key_override: str | None = None,
) -> Optional[str]:
    """
    Upload already-compressed gzip data to GCS.
    
    Key format: raw/{platform}/{YYYY}/{MM}/{DD}/{search_id}.json.gz
    
    Returns the gs:// URI or None if RAW_UPLOAD_ENABLED=false.
    """
    settings = get_settings()
    
    if not settings.RAW_UPLOAD_ENABLED:
        logger.debug(f"Raw upload disabled, skipping for search {search_id}")
        return None
    
    if key_override:
        key = key_override
    else:
        now = datetime.utcnow()
        key = f"raw/{platform}/{now.year}/{now.month:02d}/{now.day:02d}/{search_id}.json.gz"
    
    try:
        uri = await async_gcs_client.upload_compressed_gz(
            bucket_name=settings.GCS_BUCKET_RAW,
            key=key,
            compressed_data=compressed_data,
        )
        logger.info(f"Archived raw response for {platform} search {search_id}")
        return uri
    except Exception as e:
        # Retryable exception should bubble up
        if isinstance(e, (ValueError, TypeError)):
            logger.error(f"Failed to upload raw response (non-retryable): {e}")
            return None
        raise e
