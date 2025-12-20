"""Database query functions for search operations."""
import json
import hashlib
import time
import logging
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
    status: str = "running",
) -> UUID:
    """
    Insert a new search record.
    
    Returns the search_id.
    """
    search_id = uuid4()
    search_hash = compute_search_hash(query, inputs)
    
    await conn.execute(
        text("""
            INSERT INTO searches (id, user_id, query, inputs, search_hash, mode, status)
            VALUES (:id, :user_id, :query, :inputs, :search_hash, :mode, :status)
        """),
        {
            "id": search_id,
            "user_id": user_id,
            "query": query,
            "inputs": json.dumps(inputs),
            "search_hash": search_hash,
            "mode": mode,
            "status": status,
        }
    )
    return search_id


async def update_search_status(
    conn: AsyncConnection,
    search_id: UUID,
    status: str,
) -> None:
    """Update search status (running -> completed/failed)."""
    await conn.execute(
        text("UPDATE searches SET status = :status WHERE id = :id"),
        {"id": search_id, "status": status}
    )


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


async def insert_platform_calls_batch(
    conn: AsyncConnection,
    calls: List[dict],
) -> None:
    """Batch insert platform calls."""
    if not calls:
        return

    # Ensure JSON serializable
    prepared_calls = []
    for call in calls:
        prepared_calls.append({
            "id": str(call.get("id", uuid4())),
            "search_id": str(call["search_id"]),
            "platform": call["platform"],
            "request_params": call["request_params"],
            "success": call["success"],
            "http_status": call.get("http_status"),
            "error": call.get("error"),
            "duration_ms": call.get("duration_ms", 0),
            "next_cursor": call.get("next_cursor"),
            "response_gcs_uri": call.get("response_gcs_uri"),
            "response_meta": call.get("response_meta", {}),
        })

    await conn.execute(
        text("""
            INSERT INTO platform_calls (
                id, search_id, platform, request_params, success,
                http_status, error, duration_ms, next_cursor,
                response_gcs_uri, response_meta
            )
            SELECT 
                id, search_id, platform, request_params, success,
                http_status, error, duration_ms, next_cursor,
                response_gcs_uri, response_meta
            FROM jsonb_to_recordset(CAST(:data AS jsonb)) AS x(
                id uuid, search_id uuid, platform text, request_params jsonb, success boolean,
                http_status int, error text, duration_ms int, next_cursor jsonb,
                response_gcs_uri text, response_meta jsonb
            )
        """),
        {"data": json.dumps(prepared_calls)}
    )


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


async def upsert_content_items_batch(
    conn: AsyncConnection,
    items: List[NormalizedItem],
) -> dict:
    """
    Batch upsert content items.
    Returns a dict mapping (platform, external_id) -> (content_item_id, was_inserted).
    """
    if not items:
        return {}

    # Deduplicate items by (platform, external_id) to avoid SQL errors
    # Last one wins
    unique_items = {}
    for item in items:
        unique_items[(item.platform, item.external_id)] = item
    
    item_list = list(unique_items.values())
    prepared_items = []
    
    for item in item_list:
        prepared_items.append({
            "platform": item.platform,
            "external_id": item.external_id,
            "content_type": item.content_type,
            "canonical_url": item.canonical_url,
            "title": item.title,
            "primary_text": item.primary_text,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "creator_handle": item.creator_handle,
            "metrics": json.dumps(item.metrics),
            "payload": json.dumps(item.payload),
        })

    result = await conn.execute(
        text("""
            INSERT INTO content_items (
                platform, external_id, content_type, canonical_url,
                title, primary_text, published_at, creator_handle,
                metrics, payload
            )
            SELECT 
                platform, external_id, content_type, canonical_url,
                title, primary_text, 
                CAST(published_at AS TIMESTAMP WITH TIME ZONE), 
                creator_handle,
                metrics::jsonb, payload::jsonb
            FROM jsonb_to_recordset(CAST(:data AS jsonb)) AS x(
                platform text, external_id text, content_type text, canonical_url text,
                title text, primary_text text, published_at text, creator_handle text,
                metrics text, payload text
            )
            ON CONFLICT (platform, external_id) DO UPDATE SET
                metrics = EXCLUDED.metrics,
                updated_at = now(),
                title = COALESCE(content_items.title, EXCLUDED.title),
                primary_text = COALESCE(content_items.primary_text, EXCLUDED.primary_text),
                canonical_url = COALESCE(content_items.canonical_url, EXCLUDED.canonical_url),
                published_at = COALESCE(content_items.published_at, EXCLUDED.published_at)
            RETURNING id, platform, external_id, (xmax = 0) AS inserted
        """),
        {"data": json.dumps(prepared_items)}
    )
    
    mapping = {}
    for row in result.fetchall():
        mapping[(row[1], row[2])] = (row[0], row[3])
    
    return mapping


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


async def insert_search_results_batch(
    conn: AsyncConnection,
    results: List[dict],
) -> None:
    """Batch insert search results."""
    if not results:
        return

    await conn.execute(
        text("""
            INSERT INTO search_results (search_id, content_item_id, platform, rank)
            SELECT search_id, content_item_id, platform, rank
            FROM jsonb_to_recordset(CAST(:data AS jsonb)) AS x(
                search_id uuid, content_item_id uuid, platform text, rank int
            )
            ON CONFLICT (search_id, content_item_id) DO NOTHING
        """),
        {"data": json.dumps(results, default=str)}
    )


async def insert_media_assets_batch(
    conn: AsyncConnection,
    assets: List[dict],
) -> None:
    """Batch insert media assets."""
    if not assets:
        return

    prepared_assets = []
    for asset in assets:
        prepared_assets.append({
            "id": str(asset["id"]),
            "content_item_id": str(asset["content_item_id"]),
            "asset_type": asset["asset_type"],
            "source_url": asset["source_url"],
            "source_url_list": json.dumps(asset.get("source_url_list")) if asset.get("source_url_list") else None,
        })

    await conn.execute(
        text("""
            INSERT INTO media_assets (
                id, content_item_id, asset_type, source_url, source_url_list, status
            )
            SELECT 
                id, content_item_id, asset_type, source_url, source_url_list::jsonb, 'pending'
            FROM jsonb_to_recordset(CAST(:data AS jsonb)) AS x(
                id uuid, content_item_id uuid, asset_type text, source_url text, source_url_list text
            )
            ON CONFLICT (id) DO NOTHING
        """),
        {"data": json.dumps(prepared_assets)}
    )


from app.core import logger

async def get_search_by_id(
    conn: AsyncConnection,
    search_id: UUID,
) -> dict | None:
    """Get search by ID (RLS will filter by user)."""
    start_time = time.time()
    # logger = logging.getLogger("app.db.queries.search") # or generic logger
    logger.info(f"get_search_by_id: start query for {search_id}")
    
    result = await conn.execute(
        text("""
            SELECT id, user_id, query, inputs, search_hash, mode, status, created_at
            FROM searches
            WHERE id = :id
        """),
        {"id": search_id}
    )
    row = result.fetchone()
    
    duration = (time.time() - start_time) * 1000
    if not row:
        logger.warning(f"get_search_by_id: not found or RLS blocked. search_id={search_id} duration={duration:.2f}ms")
        return None
        
    logger.info(f"get_search_by_id: found search {search_id} duration={duration:.2f}ms")
    return {
        "id": row[0],
        "user_id": row[1],
        "query": row[2],
        "inputs": row[3],
        "search_hash": row[4],
        "mode": row[5],
        "status": row[6],
        "created_at": row[7],
    }


async def get_user_searches(
    conn: AsyncConnection,
    limit: int = 20,
) -> List[dict]:
    """Get user's searches, newest first (RLS will filter by user)."""
    result = await conn.execute(
        text("""
            SELECT id, query, inputs, status, created_at
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
            "status": row[3],
            "created_at": row[4],
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
    
    if not rows:
        return []
        
    # Collect content_item_ids to fetch assets in bulk
    content_item_ids = [row[1] for row in rows]
    
    # Bulk fetch assets
    # structure: SELECT ma.* FROM media_assets ma WHERE content_item_id IN (...)
    # OR join with search_results for safety if list is huge, 
    # but IN clause with a list is fine for reasonable page sizes (e.g. 100).
    # Since we paginate searches typically, this is safe.
    assets_result = await conn.execute(
        text("""
            SELECT content_item_id, id, asset_type, source_url, gcs_uri, status, sha256, mime_type, bytes
            FROM media_assets
            WHERE content_item_id = ANY(:ids)
        """),
        {"ids": content_item_ids}
    )
    all_assets = assets_result.fetchall()
    
    # Group assets by content_item_id
    from collections import defaultdict
    assets_map = defaultdict(list)
    for a in all_assets:
        assets_map[a[0]].append({
            "id": a[1],
            "asset_type": a[2],
            "source_url": a[3],
            "gcs_uri": a[4],
            "status": a[5],
            "sha256": a[6],
            "mime_type": a[7],
            "bytes": a[8],
        })
    
    items = []
    for row in rows:
        content_item_id = row[1]
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
            "assets": assets_map.get(content_item_id, []),
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



async def get_full_search_detail(conn: AsyncConnection, search_id: UUID) -> dict | None:
    """
    Fetch ALL search data in a single query:
    1. Search metadata
    2. Platform calls
    3. Results + Content Items + Metrics + Assets
    
    Returns a dict matching SearchDetailResponse structure (mostly).
    Data is aggregated using JSON_BUILD_OBJECT to avoid N+1 queries.
    """
    result = await conn.execute(
        text("""
            WITH search_data AS (
                SELECT 
                    id, query, inputs, mode, status, created_at
                FROM searches 
                WHERE id = :search_id
            ),
            calls_agg AS (
                SELECT 
                    search_id,
                    json_agg(json_build_object(
                        'id', id,
                        'platform', platform,
                        'success', success,
                        'http_status', http_status,
                        'error', error,
                        'duration_ms', duration_ms,
                        'next_cursor', next_cursor,
                        'response_meta', COALESCE(response_meta, '{}'::jsonb)
                    ) ORDER BY created_at) as calls
                FROM platform_calls
                WHERE search_id = :search_id
                GROUP BY search_id
            ),
            assets_agg AS (
                SELECT 
                    ma.content_item_id,
                    json_agg(json_build_object(
                        'id', ma.id,
                        'asset_type', ma.asset_type,
                        'status', ma.status,
                        'source_url', ma.source_url,
                        'gcs_uri', ma.gcs_uri,
                        'sha256', ma.sha256,
                        'mime_type', ma.mime_type,
                        'bytes', ma.bytes
                    )) as assets
                FROM search_results sr
                JOIN media_assets ma ON sr.content_item_id = ma.content_item_id
                WHERE sr.search_id = :search_id
                GROUP BY ma.content_item_id
            ),
            results_agg AS (
                SELECT 
                    sr.search_id,
                    json_agg(json_build_object(
                        'rank', sr.rank,
                        'content_item', json_build_object(
                            'id', ci.id,
                            'platform', ci.platform,
                            'external_id', ci.external_id,
                            'content_type', ci.content_type,
                            'canonical_url', ci.canonical_url,
                            'title', ci.title,
                            'primary_text', ci.primary_text,
                            'published_at', ci.published_at,
                            'creator_handle', ci.creator_handle,
                            'metrics', COALESCE(ci.metrics, '{}'::jsonb),
                            'payload', COALESCE(ci.payload, '{}'::jsonb)
                        ),
                        'assets', COALESCE(aa.assets, '[]'::json)
                    ) ORDER BY sr.rank) as results
                FROM search_results sr
                JOIN content_items ci ON sr.content_item_id = ci.id
                LEFT JOIN assets_agg aa ON ci.id = aa.content_item_id
                WHERE sr.search_id = :search_id
                GROUP BY sr.search_id
            )
            SELECT 
                sd.id,
                sd.query,
                sd.inputs,
                sd.mode,
                sd.status,
                sd.created_at,
                COALESCE(ca.calls, '[]'::json) as platform_calls,
                COALESCE(ra.results, '[]'::json) as results
            FROM search_data sd
            LEFT JOIN calls_agg ca ON sd.id = ca.search_id
            LEFT JOIN results_agg ra ON sd.id = ra.search_id
        """),
        {"search_id": search_id}
    )
    
    row = result.fetchone()
    if not row:
        return None
        
    return dict(row._mapping)
