"""Database query functions for content items."""
from uuid import UUID


from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing
from app.core.logging import logger
from app.services.cdn_signer import generate_signed_url



async def get_content_item_by_id(
    conn: AsyncConnection,
    content_item_id: UUID,
) -> dict | None:
    """Get a content item by ID with its video asset URL."""
    result = await conn.execute(
        text("""
            SELECT ci.id, ci.platform, ci.external_id, ci.content_type,
                   ci.canonical_url, ci.title, ci.payload
            FROM content_items ci
            WHERE ci.id = :id
        """),
        {"id": content_item_id}
    )
    row = result.fetchone()
    if not row:
        return None
    
    # Get video asset
    assets_result = await conn.execute(
        text("""
            SELECT source_url, gcs_uri, status
            FROM media_assets
            WHERE content_item_id = :id AND asset_type = 'video'
            LIMIT 1
        """),
        {"id": content_item_id}
    )
    asset_row = assets_result.fetchone()
    
    video_url = None
    if asset_row:
        # If we have a GCS URI, sign it. Otherwise fall back to source URL.
        # asset_row[1] is gcs_uri, asset_row[0] is source_url
        if asset_row[1]:
            try:
                # We do this import inside the function or at top level? 
                # Top level is better but avoiding circular imports is good. 
                # Services usually import queries, so queries importing services might be cyclical.
                # However, cdn_signer is a standalone service (mostly utils), so it should be fine.
                # Let's check imports.
                pass 
            except Exception:
                pass
            
            # Using the imported function
            video_url = generate_signed_url(asset_row[1])
        else:
            video_url = asset_row[0]

    return {
        "id": row[0],
        "platform": row[1],
        "external_id": row[2],
        "content_type": row[3],
        "canonical_url": row[4],
        "title": row[5],
        "payload": row[6],
        "video_url": video_url,
        "video_gcs_uri": asset_row[1] if asset_row else None,
    }



async def get_video_media_asset_for_content_item(
    conn: AsyncConnection,
    content_item_id: UUID,
) -> dict | None:
    """
    Get the video media asset for a content item.
    Returns the media asset dict (with id, gcs_uri, source_url) or None.
    """
    result = await conn.execute(
        text("""
            SELECT id, source_url, gcs_uri, status, asset_type
            FROM media_assets
            WHERE content_item_id = :content_item_id AND asset_type = 'video'
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"content_item_id": content_item_id}
    )
    row = result.fetchone()
    if not row:
        return None
    
    video_url = None
    if row[2]:  # gcs_uri
        video_url = generate_signed_url(row[2])
    else:
        video_url = row[1]  # source_url
    
    return {
        "id": row[0],
        "source_url": row[1],
        "gcs_uri": row[2],
        "status": row[3],
        "asset_type": row[4],
        "video_url": video_url,
    }


async def get_media_asset_by_id(
    conn: AsyncConnection,
    media_asset_id: UUID,
) -> dict | None:
    """
    Get a media asset by its ID.
    Returns the media asset dict (with gcs_uri, source_url, video_url) or None.
    """
    result = await conn.execute(
        text("""
            SELECT id, source_url, gcs_uri, status, asset_type, content_item_id
            FROM media_assets
            WHERE id = :media_asset_id
        """),
        {"media_asset_id": media_asset_id}
    )
    row = result.fetchone()
    if not row:
        return None
    
    video_url = None
    if row[2]:  # gcs_uri
        video_url = generate_signed_url(row[2])
    else:
        video_url = row[1]  # source_url
    
    return {
        "id": row[0],
        "source_url": row[1],
        "gcs_uri": row[2],
        "status": row[3],
        "asset_type": row[4],
        "content_item_id": row[5],
        "video_url": video_url,
    }



async def get_media_asset_with_content(
    conn: AsyncConnection,
    media_asset_id: UUID,
) -> dict | None:
    """
    Get a media asset by ID with full content item metadata.
    Used for the /view endpoint to populate ContentDrawer.
    """
    print(f"[get_media_asset_with_content] Querying for media_asset_id={media_asset_id}")
    result = await conn.execute(
        text("""
            SELECT 
                ma.id,
                ma.asset_type,
                ma.gcs_uri,
                ma.source_url,
                ma.status,
                ci.title,
                ci.platform,
                ci.creator_handle,
                ci.canonical_url,
                ci.published_at,
                ci.metrics,
                cover.source_url as cover_url,
                cover.gcs_uri as cover_gcs_uri
            FROM media_assets ma
            JOIN content_items ci ON ma.content_item_id = ci.id
            LEFT JOIN media_assets cover 
                ON cover.content_item_id = ci.id 
                AND cover.asset_type IN ('cover', 'thumbnail', 'image')
                AND cover.id != ma.id
            WHERE ma.id = :media_asset_id
            LIMIT 1
        """),
        {"media_asset_id": media_asset_id}
    )
    row = result.fetchone()
    logger.info(f"[get_media_asset_with_content] Row result: {row}")
    if not row:
        return None
    
    # Generate signed URLs
    video_url = None
    if row[2]:  # gcs_uri
        video_url = generate_signed_url(row[2])
    else:
        video_url = row[3]  # source_url
    
    thumbnail_url = None
    if row[12]:  # cover_gcs_uri
        thumbnail_url = generate_signed_url(row[12])
    elif row[11]:  # cover_url
        thumbnail_url = row[11]
    
    # Parse metrics
    metrics = row[10] or {}
    
    return {
        "id": str(row[0]),
        "asset_type": row[1],
        "url": video_url,
        "gcs_uri": row[2],
        "source_url": row[3],
        "status": row[4],
        "title": row[5],
        "platform": row[6],
        "creator": row[7],
        "canonical_url": row[8],
        "published_at": row[9].isoformat() if row[9] else None,
        "thumbnail_url": thumbnail_url,
        "view_count": int(metrics.get("views", 0) or metrics.get("play_count", 0) or 0),
        "like_count": int(metrics.get("likes", 0) or metrics.get("digg_count", 0) or 0),
        "comment_count": int(metrics.get("comments", 0) or 0),
        "share_count": int(metrics.get("shares", 0) or 0),
    }


