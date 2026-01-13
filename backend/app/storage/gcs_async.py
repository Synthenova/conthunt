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

    async def upload_compressed_gz(
        self,
        bucket_name: str,
        key: str,
        compressed_data: bytes,
    ) -> str:
        """
        Upload already-compressed gzip data directly.
        
        Returns the gs:// URI.
        """
        return await self.upload_blob(
            bucket_name=bucket_name,
            key=key,
            data=compressed_data,
            content_type="application/json",
        )

    async def upload_blob_streaming(
        self,
        bucket_name: str,
        key: str,
        response: "httpx.Response",
        content_type: str = "application/octet-stream",
        chunk_size: int = 8 * 1024 * 1024,  # 8MB chunks (GCS requires multiples of 256KB)
    ) -> tuple[str, str, int]:
        """
        Upload from an httpx streaming response to GCS using resumable upload.
        
        TRUE STREAMING: Each chunk is uploaded directly to GCS without buffering
        the entire file in memory. Peak memory usage is limited to chunk_size.
        
        Args:
            bucket_name: GCS bucket name
            key: Object key/path
            response: An httpx Response object (must be from a streaming request)
            content_type: MIME type for the blob
            chunk_size: Size of chunks to upload (default 8MB, must be multiple of 256KB)
        
        Returns:
            Tuple of (gcs_uri, sha256_hex, total_bytes)
        """
        import asyncio
        import hashlib
        import aiohttp
        from google.auth.transport.requests import Request
        from google.auth import default as google_auth_default
        
        alignment = 256 * 1024
        aligned_chunk_size = max(alignment, (chunk_size // alignment) * alignment)

        content_length_header = response.headers.get("Content-Length")
        transfer_encoding = response.headers.get("Transfer-Encoding", "")
        total_length: Optional[int] = None
        if content_length_header and "chunked" not in transfer_encoding.lower():
            try:
                total_length = int(content_length_header)
                if total_length < 0:
                    total_length = None
            except ValueError:
                total_length = None

        # Get credentials for GCS
        credentials, _project = google_auth_default()
        if credentials.expired or not credentials.valid:
            await asyncio.to_thread(credentials.refresh, Request())
        
        access_token = credentials.token
        
        # Step 1: Initiate resumable upload
        init_url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket_name}/o?uploadType=resumable&name={key}"
        
        async with aiohttp.ClientSession() as session:
            # Initiate resumable upload
            init_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Upload-Content-Type": content_type,
            }
            if total_length is not None:
                init_headers["X-Upload-Content-Length"] = str(total_length)

            async with session.post(
                init_url,
                headers=init_headers,
                json={"name": key},
            ) as init_response:
                if init_response.status != 200:
                    error_text = await init_response.text()
                    raise Exception(f"Failed to initiate resumable upload: {error_text}")
                upload_url = init_response.headers["Location"]
            
            # Step 2: Stream chunks to GCS
            sha256_hasher = hashlib.sha256()
            total_bytes = 0
            offset = 0

            async def upload_chunk(data: bytes, is_final: bool) -> None:
                nonlocal offset
                if is_final and len(data) == 0:
                    content_range = f"bytes */{total_length or 0}"
                else:
                    end_byte = offset + len(data) - 1
                    if total_length is None and not is_final:
                        content_range = f"bytes {offset}-{end_byte}/*"
                    else:
                        final_total = total_length if total_length is not None else offset + len(data)
                        content_range = f"bytes {offset}-{end_byte}/{final_total}"

                async with session.put(
                    upload_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Length": str(len(data)),
                        "Content-Range": content_range,
                    },
                    data=data,
                ) as chunk_response:
                    # 308 = Resume Incomplete (more chunks expected)
                    # 200/201 = Upload complete
                    if chunk_response.status not in (200, 201, 308):
                        error_text = await chunk_response.text()
                        raise Exception(f"Chunk upload failed: {chunk_response.status} - {error_text}")

                offset += len(data)

            buffer = bytearray()
            pending: Optional[bytes] = None

            async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                if not chunk:
                    continue
                sha256_hasher.update(chunk)
                total_bytes += len(chunk)
                buffer.extend(chunk)

                while len(buffer) >= alignment:
                    send_size = len(buffer) - (len(buffer) % alignment)
                    if send_size == 0:
                        break
                    if send_size > aligned_chunk_size:
                        send_size = aligned_chunk_size
                    payload = bytes(buffer[:send_size])
                    del buffer[:send_size]

                    if total_length is None:
                        if pending is not None:
                            await upload_chunk(pending, is_final=False)
                        pending = payload
                    else:
                        await upload_chunk(payload, is_final=False)

            if total_length is None:
                final_payload = b""
                if pending is not None:
                    final_payload += pending
                if buffer:
                    final_payload += bytes(buffer)
                await upload_chunk(final_payload, is_final=True)
            else:
                if buffer or total_length == 0:
                    await upload_chunk(bytes(buffer), is_final=True)

            if total_length is not None and total_bytes != total_length:
                logger.warning(
                    "Streamed upload byte count mismatch for %s (expected %s, got %s)",
                    key,
                    total_length,
                    total_bytes,
                )
        
        sha256_hex = sha256_hasher.hexdigest()
        gcs_uri = f"gs://{bucket_name}/{key}"
        
        logger.info(f"Streamed upload to {gcs_uri} ({total_bytes} bytes)")
        return gcs_uri, sha256_hex, total_bytes



async_gcs_client = AsyncGCSClient()
