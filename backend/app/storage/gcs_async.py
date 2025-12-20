"""Asynchronous Google Cloud Storage client wrapper."""
import logging
from typing import Optional

from gcloud.aio.storage import Storage

from app.core import get_settings

logger = logging.getLogger(__name__)


class AsyncGCSClient:
    """Async wrapper around Google Cloud Storage client."""

    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[Storage] = None

    async def get_client(self) -> Storage:
        """Get or create the async storage client."""
        if self._client is None:
            # Note: gcloud-aio-storage handles auth internally (ADC support)
            self._client = Storage()
        return self._client

    async def close(self):
        """Close the underlying client session."""
        if self._client:
            await self._client.close()
            self._client = None

    async def upload_blob(
        self,
        bucket_name: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload data to GCS bucket asynchronously.
        
        Returns the gs:// URI of the uploaded blob.
        """
        client = await self.get_client()
        
        try:
            await client.upload(
                bucket_name,
                key,
                data,
                content_type=content_type
            )
            logger.info(f"Uploaded to gs://{bucket_name}/{key}")
            return f"gs://{bucket_name}/{key}"
        except Exception as e:
            logger.error(f"Failed to upload to gs://{bucket_name}/{key}: {e}")
            raise

    async def upload_json_gz(
        self,
        bucket_name: str,
        key: str,
        data: dict,
    ) -> str:
        """
        Upload JSON data as gzipped file asynchronously.
        
        Returns the gs:// URI.
        """
        import gzip
        import json
        
        json_bytes = json.dumps(data, default=str).encode("utf-8")
        compressed = gzip.compress(json_bytes)
        
        return await self.upload_blob(
            bucket_name=bucket_name,
            key=key,
            data=compressed,
            content_type="application/json",
        )

async_gcs_client = AsyncGCSClient()
