"""Database query functions for content items."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


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
    
    return {
        "id": row[0],
        "platform": row[1],
        "external_id": row[2],
        "content_type": row[3],
        "canonical_url": row[4],
        "title": row[5],
        "payload": row[6],
        "video_url": asset_row[0] if asset_row else None,
        "video_gcs_uri": asset_row[1] if asset_row else None,
    }
