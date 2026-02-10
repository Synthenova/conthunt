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


async def get_search_result_items_for_media_asset_ids(
    conn: AsyncConnection,
    media_asset_ids: list[UUID],
) -> list[dict]:
    """
    Build "search result item" shaped objects for the given *video* media_asset_ids.
    This is used to render Deep Research chosen videos in the same grid as search results.

    Output shape matches what transformToMediaItem() expects:
      { rank, content_item: {...}, assets: [...] }
    """
    if not media_asset_ids:
        return []

    # 1) Resolve content items for the given media assets (video assets).
    res = await conn.execute(
        text(
            """
            SELECT
                ma.id              AS media_asset_id,
                ma.content_item_id AS content_item_id,
                ci.platform        AS platform,
                ci.external_id     AS external_id,
                ci.content_type    AS content_type,
                ci.canonical_url   AS canonical_url,
                ci.title           AS title,
                ci.primary_text    AS primary_text,
                ci.published_at    AS published_at,
                ci.creator_handle  AS creator_handle,
                ci.metrics         AS metrics
            FROM media_assets ma
            JOIN content_items ci ON ci.id = ma.content_item_id
            WHERE ma.id = ANY(:media_asset_ids)
            """
        ),
        {"media_asset_ids": media_asset_ids},
    )
    rows = res.fetchall()
    if not rows:
        return []

    # Preserve input order (by media_asset_id), but aggregate by content_item_id.
    video_asset_to_content: dict[str, str] = {}
    content_by_id: dict[str, dict] = {}
    ordered_content_ids: list[str] = []

    for r in rows:
        media_asset_id = str(r[0])
        content_item_id = str(r[1])
        video_asset_to_content[media_asset_id] = content_item_id
        if content_item_id not in content_by_id:
            content_by_id[content_item_id] = {
                "id": content_item_id,
                "platform": r[2],
                "external_id": r[3],
                "content_type": r[4],
                "canonical_url": r[5],
                "title": r[6],
                "primary_text": r[7],
                "published_at": r[8].isoformat() if r[8] else None,
                "creator_handle": r[9],
                "metrics": r[10] or {},
            }
            ordered_content_ids.append(content_item_id)

    # 2) Load assets for those content items.
    assets_res = await conn.execute(
        text(
            """
            SELECT
                id,
                content_item_id,
                asset_type,
                status,
                source_url,
                gcs_uri
            FROM media_assets
            WHERE content_item_id = ANY(:content_item_ids)
              AND asset_type IN ('video', 'cover', 'thumbnail', 'image')
            """
        ),
        {"content_item_ids": [UUID(cid) for cid in ordered_content_ids]},
    )
    asset_rows = assets_res.fetchall()

    assets_by_content: dict[str, list[dict]] = {cid: [] for cid in ordered_content_ids}
    for a in asset_rows:
        asset_id = str(a[0])
        cid = str(a[1])
        asset_type = a[2]
        status = a[3]
        source_url = a[4]
        gcs_uri = a[5]
        # If we only have GCS, provide a signed URL as source_url so the grid can render instantly.
        if (not source_url) and gcs_uri:
            try:
                source_url = generate_signed_url(gcs_uri)
            except Exception:
                source_url = None

        assets_by_content.setdefault(cid, []).append(
            {
                "id": asset_id,
                "asset_type": asset_type,
                "status": status,
                "source_url": source_url,
                "gcs_uri": gcs_uri,
            }
        )

    # 3) Build result items. Prefer to place the chosen video asset first when possible.
    def _asset_sort_key(asset: dict, preferred_video_asset_id: str | None) -> tuple[int, int]:
        # video first, then cover, then others; preferred chosen video id first among videos
        t = asset.get("asset_type")
        order = 3
        if t == "video":
            order = 0
        elif t == "cover":
            order = 1
        elif t == "thumbnail":
            order = 2
        pref = 1
        if preferred_video_asset_id and asset.get("id") == preferred_video_asset_id:
            pref = 0
        return (order, pref)

    out: list[dict] = []
    for mid in [str(x) for x in media_asset_ids]:
        cid = video_asset_to_content.get(mid)
        if not cid:
            continue
        content = content_by_id.get(cid)
        if not content:
            continue
        assets = assets_by_content.get(cid) or []
        assets_sorted = sorted(assets, key=lambda a: _asset_sort_key(a, mid))
        out.append(
            {
                "rank": 0,
                "content_item": content,
                "assets": assets_sorted,
            }
        )

    return out

