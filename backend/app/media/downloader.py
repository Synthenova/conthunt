"""Background media downloader."""
import asyncio
import hashlib
from typing import List
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import get_settings, logger
from app.storage.gcs import gcs_client
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
    Download and store a single media asset.
    
    This function handles:
    1. Downloading via httpx streaming
    2. Computing SHA256
    3. Uploading to GCS
    4. Updating the database record
    """
    from app.db.session import get_db_connection
    
    settings = get_settings()
    asset_id = asset["id"]
    source_url = asset["source_url"]
    asset_type = asset["asset_type"]
    
    try:
        # Download the file
        async with http_client.stream(
            "GET",
            source_url,
            timeout=settings.MEDIA_HTTP_TIMEOUT_S,
            follow_redirects=True,
        ) as response:
            response.raise_for_status()
            
            # Read content and compute hash
            content = await response.aread()
            sha256_hash = hashlib.sha256(content).hexdigest()
            mime_type = response.headers.get("content-type", "application/octet-stream")
            
            # Determine file extension
            ext = get_file_extension(source_url, mime_type)
            
            # Build GCS key: media/{platform}/{external_id}/{asset_type}/{sha256}.{ext}
            gcs_key = f"media/{platform}/{external_id}/{asset_type}/{sha256_hash}.{ext}"
            
            # Upload to GCS
            gcs_uri = gcs_client.upload_blob(
                bucket_name=settings.GCS_BUCKET_MEDIA,
                key=gcs_key,
                data=content,
                content_type=mime_type,
            )
            
            # Update database
            async with get_db_connection() as conn:
                await update_asset_stored(
                    conn=conn,
                    asset_id=asset_id,
                    gcs_uri=gcs_uri,
                    sha256=sha256_hash,
                    mime_type=mime_type,
                    size_bytes=len(content),
                )
            
            logger.info(f"Downloaded and stored asset {asset_id}: {gcs_uri}")
            
    except Exception as e:
        logger.error(f"Failed to download asset {asset_id}: {e}")
        async with get_db_connection() as conn:
            await update_asset_failed(conn, asset_id, str(e))


async def download_asset_with_claim(
    http_client: httpx.AsyncClient,
    asset_id: UUID,
    platform: str,
    external_id: str,
) -> None:
    """Download asset with claim check and semaphore."""
    from app.db.session import get_db_connection
    
    settings = get_settings()
    
    if not settings.MEDIA_DOWNLOAD_ENABLED:
        logger.debug(f"Media download disabled, skipping asset {asset_id}")
        return
    
    semaphore = get_download_semaphore()
    
    async with semaphore:
        # Try to claim the asset
        async with get_db_connection() as conn:
            asset = await claim_asset_for_download(conn, asset_id)
        
        if not asset:
            logger.debug(f"Asset {asset_id} already claimed or processed")
            return
        
        await download_single_asset(http_client, asset, platform, external_id)


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
        logger.info(f"Media download disabled, skipping {len(asset_infos)} assets")
        return
    
    logger.info(f"Starting background download of {len(asset_infos)} assets")
    
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
