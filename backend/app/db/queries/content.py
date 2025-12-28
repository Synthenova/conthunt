"""Database query functions for content items."""
from uuid import UUID


from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.decorators import log_query_timing

from app.services.cdn_signer import generate_signed_url


@log_query_timing
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


@log_query_timing
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


@log_query_timing
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

