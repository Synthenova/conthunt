"""Google Cloud Storage client wrapper."""
import gzip
import json
from datetime import timedelta
from typing import Optional

from google.cloud import storage

from app.core import get_settings, logger


class GCSClient:
    """Wrapper around Google Cloud Storage client."""

    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[storage.Client] = None

    @property
    def client(self) -> storage.Client:
        if self._client is None:
            self._client = storage.Client(project=self.settings.GCP_PROJECT)
        return self._client

    def upload_blob(
        self,
        bucket_name: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        content_encoding: Optional[str] = None,
    ) -> str:
        """
        Upload data to GCS bucket.
        
        Returns the gs:// URI of the uploaded blob.
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(key)
        blob.content_type = content_type
        if content_encoding:
            blob.content_encoding = content_encoding
        blob.upload_from_string(data, content_type=content_type)
        logger.info(f"Uploaded to gs://{bucket_name}/{key}")
        return f"gs://{bucket_name}/{key}"

    def upload_json_gz(
        self,
        bucket_name: str,
        key: str,
        data: dict,
    ) -> str:
        """
        Upload JSON data as gzipped file.
        
        Returns the gs:// URI.
        """
        json_bytes = json.dumps(data, default=str).encode("utf-8")
        compressed = gzip.compress(json_bytes)
        return self.upload_blob(
            bucket_name=bucket_name,
            key=key,
            data=compressed,
            content_type="application/json",
            content_encoding="gzip",
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
        # Parse gs://bucket/key format
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        parts = gcs_uri[5:].split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
        
        bucket_name, key = parts
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(key)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration_seconds),
            method="GET",
        )
        return url

    def download_blob(self, gcs_uri: str) -> bytes:
        """Download blob contents."""
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        parts = gcs_uri[5:].split("/", 1)
        bucket_name, key = parts
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(key)
        return blob.download_as_bytes()


# Singleton instance
gcs_client = GCSClient()
