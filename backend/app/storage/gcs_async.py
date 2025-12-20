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

    def generate_signed_url(
        self,
        gcs_uri: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """
        Generate a signed URL for the given gs:// URI.
        
        Args:
            gcs_uri: Full gs:// URI (e.g., gs://bucket/path/to/file)
            expiration_seconds: URL validity in seconds (default 1 hour)
            
        Returns:
            Signed URL string
        """
        # Lazy import to avoid sync client overhead on module load
        from google.cloud import storage
        from datetime import timedelta
        
        # Parse gs://bucket/key format
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        parts = gcs_uri[5:].split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
        
        bucket_name, key = parts
        
        # We instantiate a client just for signing. 
        # This uses ADC but doesn't necessarily block if we don't make requests.
        client = storage.Client(project=self.settings.GCP_PROJECT)
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(key)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration_seconds),
            method="GET",
        )
        return url# Singleton instance
async_gcs_client = AsyncGCSClient()
