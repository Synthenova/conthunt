"""Raw API response archival to GCS."""
from datetime import datetime
from uuid import UUID
from typing import Optional

from app.core import get_settings, logger
from app.storage.gcs import gcs_client


async def upload_raw_json_gz(
    platform: str,
    search_id: UUID,
    raw_json: dict,
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
    
    now = datetime.utcnow()
    key = f"raw/{platform}/{now.year}/{now.month:02d}/{now.day:02d}/{search_id}.json.gz"
    
    try:
        uri = gcs_client.upload_json_gz(
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
