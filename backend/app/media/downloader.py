"""Background media downloader."""
import asyncio
import hashlib
import json
from io import BytesIO
from typing import Any, List

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


async def claim_assets_for_download_batch(
    conn: AsyncConnection,
    asset_ids: List[UUID],
) -> list[dict]:
    """
    Atomically claim many assets for download in one statement.

    Returns claimed rows only (assets already claimed/processed are skipped).
    """
    if not asset_ids:
        return []

    result = await conn.execute(
        text(
            """
            UPDATE media_assets
            SET status = 'downloading'
            WHERE id = ANY(:asset_ids) AND status = 'pending'
            RETURNING id, content_item_id, asset_type, source_url, source_url_list
            """
        ),
        {"asset_ids": asset_ids},
    )
    rows = result.fetchall()
    return [
        {
            "id": row[0],
            "content_item_id": row[1],
            "asset_type": row[2],
            "source_url": row[3],
            "source_url_list": row[4],
        }
        for row in rows
    ]


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
              AND status = 'downloading'
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


async def update_assets_stored_batch(
    conn: AsyncConnection,
    rows: list[dict[str, Any]],
) -> None:
    """
    rows format:
      [{"asset_id": UUID, "gcs_uri": str|None, "sha256": str|None, "mime_type": str|None, "size_bytes": int|None}, ...]
    """
    if not rows:
        return

    payload = [
        {
            "asset_id": str(row["asset_id"]),
            "gcs_uri": row.get("gcs_uri"),
            "sha256": row.get("sha256"),
            "mime_type": row.get("mime_type"),
            "bytes": row.get("size_bytes"),
        }
        for row in rows
    ]
    await conn.execute(
        text(
            """
            UPDATE media_assets ma
            SET status = 'stored',
                gcs_uri = x.gcs_uri,
                sha256 = x.sha256,
                mime_type = x.mime_type,
                bytes = x.bytes
            FROM jsonb_to_recordset(CAST(:payload AS jsonb)) AS x(
                asset_id uuid, gcs_uri text, sha256 text, mime_type text, bytes bigint
            )
            WHERE ma.id = x.asset_id
              AND ma.status = 'downloading'
            """
        ),
        {"payload": json.dumps(payload)},
    )


async def update_assets_failed_batch(
    conn: AsyncConnection,
    rows: list[dict[str, Any]],
) -> None:
    """
    rows format:
      [{"asset_id": UUID, "error": str}, ...]
    """
    if not rows:
        return

    payload = [
        {
            "asset_id": str(row["asset_id"]),
            "error": str(row.get("error") or "Download failed")[:1000],
        }
        for row in rows
    ]
    await conn.execute(
        text(
            """
            UPDATE media_assets ma
            SET status = 'failed',
                error = x.error
            FROM jsonb_to_recordset(CAST(:payload AS jsonb)) AS x(
                asset_id uuid, error text
            )
            WHERE ma.id = x.asset_id
            """
        ),
        {"payload": json.dumps(payload)},
    )


async def reset_assets_pending_batch(
    conn: AsyncConnection,
    asset_ids: list[UUID],
) -> None:
    """
    Reset assets to pending for retry.
    """
    if not asset_ids:
        return
    await conn.execute(
        text(
            """
            UPDATE media_assets
            SET status = 'pending',
                error = NULL
            WHERE id = ANY(:asset_ids)
            """
        ),
        {"asset_ids": asset_ids},
    )


async def download_single_asset_data(
    http_client: httpx.AsyncClient,
    asset: dict,
    platform: str,
    external_id: str,
) -> dict[str, Any]:
    """
    Download and store a single media asset using streaming upload.
    
    Streams directly from source URL to GCS without loading entire file into RAM.
    Exceptions are propagated to allow Cloud Tasks retries.
    """
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
            final_mime_type = out_mime_type
        else:
            # Use asset_id in key (hash is stored in DB for deduplication)
            gcs_key = f"media/{platform}/{external_id}/{asset_type}/{asset_id}.{ext}"
            gcs_uri, sha256_hash, size_bytes = await async_gcs_client.upload_blob_streaming(
                bucket_name=settings.GCS_BUCKET_MEDIA,
                key=gcs_key,
                response=response,
                content_type=mime_type,
            )
            final_mime_type = mime_type
        # --- End optional image optimization ---

        return {
            "asset_id": asset_id,
            "gcs_uri": gcs_uri,
            "sha256": sha256_hash,
            "mime_type": final_mime_type,
            "size_bytes": size_bytes,
        }


async def download_single_asset(
    http_client: httpx.AsyncClient,
    asset: dict,
    platform: str,
    external_id: str,
) -> None:
    """
    Backward-compatible single-asset helper that still writes DB status directly.
    """
    from app.db.session import get_db_connection

    stored = await download_single_asset_data(
        http_client=http_client,
        asset=asset,
        platform=platform,
        external_id=external_id,
    )
    async with get_db_connection() as conn:
        await update_asset_stored(
            conn=conn,
            asset_id=stored["asset_id"],
            gcs_uri=stored["gcs_uri"],
            sha256=stored["sha256"],
            mime_type=stored["mime_type"],
            size_bytes=stored["size_bytes"],
        )


async def download_claimed_asset(
    http_client: httpx.AsyncClient,
    asset: dict,
    platform: str,
    external_id: str,
) -> dict[str, Any]:
    """
    Download an already-claimed asset and return row data for bulk DB updates.
    """
    if platform == "youtube" and asset.get("asset_type") == "video":
        return {
            "asset_id": asset["id"],
            "gcs_uri": None,
            "sha256": None,
            "mime_type": None,
            "size_bytes": None,
        }
    return await download_single_asset_data(
        http_client=http_client,
        asset=asset,
        platform=platform,
        external_id=external_id,
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
                          AND status = 'downloading'
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
