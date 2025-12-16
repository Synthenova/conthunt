"""Database query functions for search operations."""
import json
import hashlib
from typing import List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.platforms.base import NormalizedItem, MediaUrl


def compute_search_hash(query: str, inputs: dict) -> str:
    """Compute a deterministic hash for a search request."""
    canonical = json.dumps({"query": query, "inputs": inputs}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


async def insert_search(
    conn: AsyncConnection,
    user_id: UUID,
    query: str,
    inputs: dict,
    mode: str = "live",
) -> UUID:
    """
    Insert a new search record.
    
    Returns the search_id.
    """
    search_id = uuid4()
    search_hash = compute_search_hash(query, inputs)
    
    await conn.execute(
        text("""
            INSERT INTO searches (id, user_id, query, inputs, search_hash, mode)
            VALUES (:id, :user_id, :query, :inputs, :search_hash, :mode)
        """),
        {
            "id": search_id,
            "user_id": user_id,
            "query": query,
            "inputs": json.dumps(inputs),
            "search_hash": search_hash,
            "mode": mode,
        }
    )
    return search_id


async def insert_platform_call(
    conn: AsyncConnection,
    search_id: UUID,
    platform: str,
    request_params: dict,
    success: bool,
    http_status: int | None = None,
    error: str | None = None,
    duration_ms: int = 0,
    next_cursor: dict | None = None,
    response_gcs_uri: str | None = None,
    response_meta: dict | None = None,
) -> UUID:
    """
    Insert a platform call record.
    
    Returns the platform_call id.
    """
    call_id = uuid4()
    
    await conn.execute(
        text("""
            INSERT INTO platform_calls (
                id, search_id, platform, request_params, success,
                http_status, error, duration_ms, next_cursor,
                response_gcs_uri, response_meta
            )
            VALUES (
                :id, :search_id, :platform, :request_params, :success,
                :http_status, :error, :duration_ms, :next_cursor,
                :response_gcs_uri, :response_meta
            )
        """),
        {
            "id": call_id,
            "search_id": search_id,
            "platform": platform,
            "request_params": json.dumps(request_params),
            "success": success,
            "http_status": http_status,
            "error": error,
            "duration_ms": duration_ms,
            "next_cursor": json.dumps(next_cursor) if next_cursor else None,
            "response_gcs_uri": response_gcs_uri,
            "response_meta": json.dumps(response_meta or {}),
        }
    )
    return call_id


async def upsert_content_item(
    conn: AsyncConnection,
    item: NormalizedItem,
) -> Tuple[UUID, bool]:
    """
    Upsert a content item.
    
    Returns (content_item_id, was_inserted).
    Uses the xmax = 0 trick to determine if row was newly inserted.
    """
    result = await conn.execute(
        text("""
            INSERT INTO content_items (
                platform, external_id, content_type, canonical_url,
                title, primary_text, published_at, creator_handle,
                metrics, payload
            )
            VALUES (
                :platform, :external_id, :content_type, :canonical_url,
                :title, :primary_text, :published_at, :creator_handle,
                :metrics, :payload
            )
            ON CONFLICT (platform, external_id) DO UPDATE SET
                metrics = EXCLUDED.metrics,
                updated_at = now(),
                title = COALESCE(content_items.title, EXCLUDED.title),
                primary_text = COALESCE(content_items.primary_text, EXCLUDED.primary_text),
                canonical_url = COALESCE(content_items.canonical_url, EXCLUDED.canonical_url),
                published_at = COALESCE(content_items.published_at, EXCLUDED.published_at)
            RETURNING id, (xmax = 0) AS inserted
        """),
        {
            "platform": item.platform,
            "external_id": item.external_id,
            "content_type": item.content_type,
            "canonical_url": item.canonical_url,
            "title": item.title,
            "primary_text": item.primary_text,
            "published_at": item.published_at,
            "creator_handle": item.creator_handle,
            "metrics": json.dumps(item.metrics),
            "payload": json.dumps(item.payload),
        }
    )
    row = result.fetchone()
    return row[0], row[1]


async def insert_search_result(
    conn: AsyncConnection,
    search_id: UUID,
    content_item_id: UUID,
    platform: str,
    rank: int,
) -> None:
    """Insert a search result linking search to content item."""
    await conn.execute(
        text("""
            INSERT INTO search_results (search_id, content_item_id, platform, rank)
            VALUES (:search_id, :content_item_id, :platform, :rank)
            ON CONFLICT (search_id, content_item_id) DO NOTHING
        """),
        {
            "search_id": search_id,
            "content_item_id": content_item_id,
            "platform": platform,
            "rank": rank,
        }
    )


async def insert_media_asset(
    conn: AsyncConnection,
    content_item_id: UUID,
    media_url: MediaUrl,
) -> UUID:
    """
    Insert a pending media asset.
    
    Returns the asset_id.
    """
    asset_id = uuid4()
    
    await conn.execute(
        text("""
            INSERT INTO media_assets (
                id, content_item_id, asset_type, source_url, source_url_list, status
            )
            VALUES (:id, :content_item_id, :asset_type, :source_url, :source_url_list, 'pending')
        """),
        {
            "id": asset_id,
            "content_item_id": content_item_id,
            "asset_type": media_url.asset_type.value,
            "source_url": media_url.source_url,
            "source_url_list": json.dumps(media_url.source_url_list) if media_url.source_url_list else None,
        }
    )
    return asset_id


async def get_search_by_id(
    conn: AsyncConnection,
    search_id: UUID,
) -> dict | None:
    """Get search by ID (RLS will filter by user)."""
    result = await conn.execute(
        text("""
            SELECT id, user_id, query, inputs, search_hash, mode, created_at
            FROM searches
            WHERE id = :id
        """),
        {"id": search_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "user_id": row[1],
        "query": row[2],
        "inputs": row[3],
        "search_hash": row[4],
        "mode": row[5],
        "created_at": row[6],
    }


async def get_user_searches(
    conn: AsyncConnection,
    limit: int = 20,
) -> List[dict]:
    """Get user's searches, newest first (RLS will filter by user)."""
    result = await conn.execute(
        text("""
            SELECT id, query, inputs, created_at
            FROM searches
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )
    rows = result.fetchall()
    return [
        {
            "id": row[0],
            "query": row[1],
            "inputs": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]


async def get_platform_calls_for_search(
    conn: AsyncConnection,
    search_id: UUID,
) -> List[dict]:
    """Get platform calls for a search."""
    result = await conn.execute(
        text("""
            SELECT id, platform, request_params, success, http_status, 
                   error, duration_ms, next_cursor, response_gcs_uri, response_meta
            FROM platform_calls
            WHERE search_id = :search_id
        """),
        {"search_id": search_id}
    )
    rows = result.fetchall()
    return [
        {
            "id": row[0],
            "platform": row[1],
            "request_params": row[2],
            "success": row[3],
            "http_status": row[4],
            "error": row[5],
            "duration_ms": row[6],
            "next_cursor": row[7],
            "response_gcs_uri": row[8],
            "response_meta": row[9],
        }
        for row in rows
    ]


async def get_search_results_with_content(
    conn: AsyncConnection,
    search_id: UUID,
) -> List[dict]:
    """Get search results with content items and media assets."""
    result = await conn.execute(
        text("""
            SELECT 
                sr.rank,
                ci.id, ci.platform, ci.external_id, ci.content_type,
                ci.canonical_url, ci.title, ci.primary_text, ci.published_at,
                ci.creator_handle, ci.metrics, ci.payload
            FROM search_results sr
            JOIN content_items ci ON sr.content_item_id = ci.id
            WHERE sr.search_id = :search_id
            ORDER BY sr.rank
        """),
        {"search_id": search_id}
    )
    rows = result.fetchall()
    
    items = []
    for row in rows:
        content_item_id = row[1]
        
        # Get media assets for this content item
        assets_result = await conn.execute(
            text("""
                SELECT id, asset_type, source_url, gcs_uri, status, sha256, mime_type, bytes
                FROM media_assets
                WHERE content_item_id = :content_item_id
            """),
            {"content_item_id": content_item_id}
        )
        assets = [
            {
                "id": a[0],
                "asset_type": a[1],
                "source_url": a[2],
                "gcs_uri": a[3],
                "status": a[4],
                "sha256": a[5],
                "mime_type": a[6],
                "bytes": a[7],
            }
            for a in assets_result.fetchall()
        ]
        
        items.append({
            "rank": row[0],
            "content_item": {
                "id": row[1],
                "platform": row[2],
                "external_id": row[3],
                "content_type": row[4],
                "canonical_url": row[5],
                "title": row[6],
                "primary_text": row[7],
                "published_at": row[8],
                "creator_handle": row[9],
                "metrics": row[10],
                "payload": row[11],
            },
            "assets": assets,
        })
    
    return items


async def get_media_asset_with_access_check(
    conn: AsyncConnection,
    asset_id: UUID,
) -> dict | None:
    """
    Get media asset verifying user has access through RLS-protected tables.
    
    Joins through search_results -> searches (RLS protected) to verify access.
    """
    result = await conn.execute(
        text("""
            SELECT ma.id, ma.gcs_uri, ma.status, ma.asset_type, ma.mime_type
            FROM media_assets ma
            JOIN content_items ci ON ma.content_item_id = ci.id
            JOIN search_results sr ON sr.content_item_id = ci.id
            JOIN searches s ON sr.search_id = s.id
            WHERE ma.id = :asset_id
            LIMIT 1
        """),
        {"asset_id": asset_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "gcs_uri": row[1],
        "status": row[2],
        "asset_type": row[3],
        "mime_type": row[4],
    }
