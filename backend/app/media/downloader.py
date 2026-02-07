"""Background media downloader."""
import asyncio
import hashlib
from io import BytesIO
from typing import List

from uuid import UUID

import httpx
from PIL import Image
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import get_settings, logger
from app.storage.gcs_async import async_gcs_client
from app.media.extractor import get_file_extension


# Module-level semaphore for concurrency control
_download_semaphore: asyncio.Semaphore | None = None


def get_download_semaphore() -> asyncio.Semaphore:
    """Get or create the download semaphore."""
    global _download_semaphore
    if _download_semaphore is None:
        settings = get_settings()
        _download_semaphore = asyncio.Semaphore(settings.MEDIA_MAX_CONCURRENCY)
    return _download_semaphore


def _should_optimize_image(asset_type: str, mime_type: str) -> bool:
    settings = get_settings()
    if not settings.MEDIA_OPTIMIZE_IMAGES:
        return False
    if not mime_type or not mime_type.startswith("image/"):
        return False
    return asset_type in {"thumbnail", "cover", "image"}


def _optimize_image_bytes(raw_bytes: bytes) -> tuple[bytes, str, str]:
    settings = get_settings()
    target_format = settings.MEDIA_IMAGE_FORMAT.lower().strip()
    quality = settings.MEDIA_IMAGE_QUALITY

    with Image.open(BytesIO(raw_bytes)) as img:
        img.load()

        if target_format in {"jpeg", "jpg"}:
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGB")
            out_format = "JPEG"
            out_mime = "image/jpeg"
            out_ext = "jpg"
            save_kwargs = {"quality": quality, "optimize": True, "progressive": True}
        else:
            out_format = "WEBP"
            out_mime = "image/webp"
            out_ext = "webp"
            save_kwargs = {"quality": quality}

        output = BytesIO()
        img.save(output, format=out_format, **save_kwargs)
        return output.getvalue(), out_mime, out_ext


async def claim_asset_for_download(
    conn: AsyncConnection,
    asset_id: UUID,
) -> dict | None:
    """
    Atomically claim an asset for download.
    
    Returns the asset row if successfully claimed, None if already claimed/processed.
    """
    result = await conn.execute(
        text("""
            UPDATE media_assets 
            SET status = 'downloading'
            WHERE id = :id AND status = 'pending'
            RETURNING id, content_item_id, asset_type, source_url, source_url_list
        """),
        {"id": asset_id}
    )
    row = result.fetchone()
    if row:
        await conn.commit()
        return {
            "id": row[0],
            "content_item_id": row[1],
            "asset_type": row[2],
            "source_url": row[3],
            "source_url_list": row[4],
        }
    return None


async def update_asset_stored(
    conn: AsyncConnection,
    asset_id: UUID,
    gcs_uri: str,
    sha256: str,
    mime_type: str,
    size_bytes: int,
) -> None:
    """Mark asset as successfully stored."""
    await conn.execute(
        text("""
            UPDATE media_assets 
            SET status = 'stored',
                gcs_uri = :gcs_uri,
                sha256 = :sha256,
                mime_type = :mime_type,
                bytes = :bytes
            WHERE id = :id
        """),
        {
            "id": asset_id,
            "gcs_uri": gcs_uri,
            "sha256": sha256,
            "mime_type": mime_type,
            "bytes": size_bytes,
        }
    )
    await conn.commit()


async def update_asset_failed(
    conn: AsyncConnection,
    asset_id: UUID,
    error: str,
) -> None:
    """Mark asset as failed."""
    await conn.execute(
        text("""
            UPDATE media_assets 
            SET status = 'failed',
                error = :error
            WHERE id = :id
        """),
        {"id": asset_id, "error": error[:1000]}  # Truncate error
    )
    await conn.commit()


async def download_single_asset(
    http_client: httpx.AsyncClient,
    asset: dict,
    platform: str,
    external_id: str,
) -> None:
    """
    Download and store a single media asset using streaming upload.
    
    Streams directly from source URL to GCS without loading entire file into RAM.
    Exceptions are propagated to allow Cloud Tasks retries.
    """
    from app.db.session import get_db_connection
    
    settings = get_settings()
    asset_id = asset["id"]
    source_url = asset["source_url"]
    asset_type = asset["asset_type"]
    
    # Stream download directly to GCS
    async with http_client.stream(
        "GET",
        source_url,
        timeout=settings.MEDIA_HTTP_TIMEOUT_S,
        follow_redirects=True,
    ) as response:
        response.raise_for_status()
        
        mime_type = response.headers.get("content-type", "application/octet-stream")
        
        # Determine file extension
        ext = get_file_extension(source_url, mime_type)

        # --- Optional image optimization (comment out this block to revert to streaming) ---
        if _should_optimize_image(asset_type, mime_type):
            raw_bytes = await response.aread()
            out_mime_type = mime_type
            out_ext = ext
            upload_bytes = raw_bytes

            try:
                optimized_bytes, out_mime_type, out_ext = _optimize_image_bytes(raw_bytes)
                upload_bytes = optimized_bytes
            except Exception as exc:
                pass
                # logger.warning(
                #     "Image optimize failed for asset %s, uploading original bytes: %s",
                #     asset_id,
                #     exc,
                # )

            gcs_key = f"media/{platform}/{external_id}/{asset_type}/{asset_id}.{out_ext}"
            gcs_uri = await async_gcs_client.upload_blob(
                bucket_name=settings.GCS_BUCKET_MEDIA,
                key=gcs_key,
                data=upload_bytes,
                content_type=out_mime_type,
            )
            sha256_hash = hashlib.sha256(upload_bytes).hexdigest()
            size_bytes = len(upload_bytes)
        else:
            # Use asset_id in key (hash is stored in DB for deduplication)
            gcs_key = f"media/{platform}/{external_id}/{asset_type}/{asset_id}.{ext}"
            gcs_uri, sha256_hash, size_bytes = await async_gcs_client.upload_blob_streaming(
                bucket_name=settings.GCS_BUCKET_MEDIA,
                key=gcs_key,
                response=response,
                content_type=mime_type,
            )
        # --- End optional image optimization ---
        
        # Update database
        async with get_db_connection() as conn:
            await update_asset_stored(
                conn=conn,
                asset_id=asset_id,
                gcs_uri=gcs_uri,
                sha256=sha256_hash,
                mime_type=mime_type,
                size_bytes=size_bytes,
            )




async def download_asset_with_claim(
    http_client: httpx.AsyncClient,
    asset_id: UUID,
    platform: str,
    external_id: str,
    skip_semaphore: bool = False,
) -> None:
    """Download asset with claim check and optional semaphore.
    
    Args:
        skip_semaphore: If True, bypass concurrency limit (for priority downloads).
    """
    from app.db.session import get_db_connection
    
    settings = get_settings()
    
    if not settings.MEDIA_DOWNLOAD_ENABLED:
        logger.debug(f"Media download disabled, skipping asset {asset_id}")
        return
    
    async def _do_download():
        # Try to claim the asset
        async with get_db_connection() as conn:
            asset = await claim_asset_for_download(conn, asset_id)
        
        if not asset:
            logger.debug(f"Asset {asset_id} already claimed or processed")
            return
        
        # YouTube video assets: mark as stored without downloading
        # YouTube URLs are HTML pages, not direct video files
        if platform == "youtube" and asset.get("asset_type") == "video":
            logger.debug(f"YouTube video asset {asset_id} - marking stored without download")
            async with get_db_connection() as conn:
                await conn.execute(
                    text("""
                        UPDATE media_assets 
                        SET status = 'stored'
                        WHERE id = :id
                    """),
                    {"id": asset_id}
                )
                await conn.commit()
            return
        
        await download_single_asset(http_client, asset, platform, external_id)
    
    if skip_semaphore:
        # Priority download: bypass semaphore
        logger.debug(f"[PRIORITY] Downloading asset {asset_id} without semaphore")
        await _do_download()
    else:
        # Normal download: respect semaphore
        semaphore = get_download_semaphore()
        async with semaphore:
            await _do_download()



async def download_assets_batch(
    asset_infos: List[dict],
) -> None:
    """
    Download a batch of assets in parallel (with concurrency limit).
    
    Args:
        asset_infos: List of dicts with {id, platform, external_id}
    """
    if not asset_infos:
        return
    
    settings = get_settings()
    
    if not settings.MEDIA_DOWNLOAD_ENABLED:
        logger.debug(f"Media download disabled, skipping {len(asset_infos)} assets")
        return
    
    logger.debug(f"Starting background download of {len(asset_infos)} assets")
    
    async with httpx.AsyncClient(
        timeout=settings.MEDIA_HTTP_TIMEOUT_S,
        follow_redirects=True,
    ) as client:
        tasks = [
            download_asset_with_claim(
                http_client=client,
                asset_id=info["id"],
                platform=info["platform"],
                external_id=info["external_id"],
            )
            for info in asset_infos
        ]
        
        # Run with gather, ignoring individual failures
        await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info(f"Completed background download batch")
