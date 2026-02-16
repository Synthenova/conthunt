"""Search API endpoint - POST /v1/search with Redis streaming."""
import asyncio
import time
from datetime import datetime
from typing import List
import uuid
from uuid import UUID
import traceback

import httpx
import json
import redis.asyncio as redis
from sqlalchemy import text
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter, Depends, HTTPException, Request, Header

from app.auth import get_current_user
from app.core import get_settings, logger
from app.core.redis_client import get_app_redis
from app.core.telemetry import trace_span
from app.db import get_db_connection, set_rls_user, queries
from app.integrations.posthog_client import capture_event

from app.platforms import (
    PLATFORM_ADAPTERS,
    get_adapter,
    PlatformCallResult,
)
from app.platforms.registry import normalize_platform_slug
from app.storage import upload_raw_json_gz
from app.media import download_assets_batch
from app.schemas import SearchRequest, LoadMoreRequest
from app.services.cloud_tasks import cloud_tasks
from app.services.cdn_signer import bulk_sign_gcs_uris, should_sign_asset
from app.realtime.stream_hub import stream_id_gt

router = APIRouter()

def _is_terminal_payload(payload_str: str | None) -> bool:
    if not payload_str:
        return False
    return ('"type": "done"' in payload_str) or ('"type": "error"' in payload_str)


@trace_span("search.call_platform")
async def call_platform(
    client: httpx.AsyncClient,
    slug: str,
    query: str,
    params: dict,
) -> PlatformCallResult:
    """Call a single platform and return result."""
    adapter = get_adapter(slug)
    request_params = {"query": query, **params}
    
    start_time = time.time()
    try:
        raw_response = await adapter.fetch(client, query, params)
        duration_ms = int((time.time() - start_time) * 1000)
        parsed = adapter.parse(raw_response)
        
        return PlatformCallResult(
            platform=slug,
            success=True,
            parsed=parsed,
            http_status=200,
            duration_ms=duration_ms,
            request_params=request_params,
        )
    except httpx.HTTPStatusError as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Platform {slug} HTTP error: {e}")
        return PlatformCallResult(
            platform=slug,
            success=False,
            http_status=e.response.status_code,
            error=str(e),
            duration_ms=duration_ms,
            request_params=request_params,
        )
    except Exception as e:
        logger.error(f"Platform {slug} error traceback:\n{traceback.format_exc()}")
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Platform {slug} error: {e}")
        return PlatformCallResult(
            platform=slug,
            success=False,
            error=str(e),
            duration_ms=duration_ms,
            request_params=request_params,
        )


@trace_span("search.transform_result_to_stream_item")
def transform_result_to_stream_item(result: PlatformCallResult) -> dict:
    """Transform a platform result to the format expected by frontend stream."""
    items_data = []
    if result.parsed:
        for item in result.parsed.items:
            # Generate deterministic ID for content item
            content_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{item.platform}:{item.external_id}"))

            # Construct assets list
            assets_data = []
            for media in item.media_urls:
                asset_seed = f"{content_id}:{media.asset_type.value}:{media.source_url}"
                asset_id = str(uuid.uuid5(uuid.NAMESPACE_URL, asset_seed))

                assets_data.append({
                    "id": asset_id, 
                    "asset_type": media.asset_type.value,
                    "status": "pending",
                    "source_url": media.source_url,
                    "gcs_uri": None
                })

            items_data.append({
                "rank": 0,
                "content_item": {
                    "id": content_id,
                    "platform": item.platform,
                    "external_id": item.external_id,
                    "content_type": item.content_type,
                    "canonical_url": item.canonical_url,
                    "title": item.title,
                    "primary_text": item.primary_text,
                    "published_at": item.published_at,
                    "creator_handle": item.creator_handle,
                    "author_id": item.author_id,
                    "author_name": item.author_name,
                    "author_url": item.author_url,
                    "author_image_url": item.author_image_url,
                    "metrics": item.metrics,
                },
                "assets": assets_data
            })

    return {
        "type": "platform_result",
        "platform": normalize_platform_slug(result.platform),
        "success": result.success,
        "duration_ms": result.duration_ms,
        "count": len(result.parsed.items) if result.parsed else 0,
        "items": items_data,
        "error": result.error,
        "next_cursor": result.parsed.next_cursor if result.parsed else None,
    }


@trace_span("search.worker")
async def search_worker(
    search_id: UUID,
    user_uuid: UUID,
    query: str,
    inputs: dict,
    redis_client: redis.Redis,
    dispatched_at: float | None = None,
):
    """
    Background worker that:
    1. Fetches all platforms and pushes results to Redis
    2. Immediately pushes "done" to Redis (frontend stops loading)
    3. Saves to DB and updates status
    4. Fire-and-forget: uploads and media downloads
    """
    settings = get_settings()
    r = redis_client
    stream_key = f"search:{search_id}:stream"
    stream_maxlen = settings.REDIS_STREAM_MAXLEN_SEARCH
    
    start_time = time.time()
    queue_duration_ms = 0
    if dispatched_at:
        queue_duration_ms = int((start_time - dispatched_at) * 1000)

    # Telemetry: Search Started
    capture_event(
        distinct_id=str(user_uuid),
        event="search_started",
        properties={
            "search_id": str(search_id),
            "queue_duration_ms": queue_duration_ms,
            "platform_count": len(inputs),
            "platforms": list(inputs.keys()),
        }
    )
    
    collected_results: List[PlatformCallResult] = []
    
    try:
        # Push start event
        await r.xadd(
            stream_key,
            {"data": json.dumps({
                "type": "start",
                "platforms": [normalize_platform_slug(slug) for slug in inputs.keys()],
                "search_id": str(search_id),
            })},
            maxlen=stream_maxlen,
            approximate=True,
        )
        
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            # Create all platform tasks
            tasks = [
                call_platform(client, slug, query, params)
                for slug, params in inputs.items()
            ]
            
            # Process as they complete
            for coro in asyncio.as_completed(tasks):
                result: PlatformCallResult = await coro
                collected_results.append(result)
                
                # Transform and push to Redis
                event_data = transform_result_to_stream_item(result)
                await r.xadd(
                    stream_key,
                    {"data": json.dumps(event_data, default=str)},
                    maxlen=stream_maxlen,
                    approximate=True,
                )
        
        # ========== DB WORK (happens after frontend is done) ==========
        assets_to_download = []
        raw_uris_by_platform: dict[str, str] = {}

        for result in collected_results:
            if result.success and result.parsed:
                now = datetime.utcnow()
                gcs_key = f"raw/{result.platform}/{now.year}/{now.month:02d}/{now.day:02d}/{search_id}.json.gz"
                try:
                    gcs_uri = await upload_raw_json_gz(
                        platform=result.platform,
                        search_id=search_id,
                        raw_json=result.parsed.raw_response,
                        key_override=gcs_key,
                    )
                    if gcs_uri:
                        raw_uris_by_platform[result.platform] = gcs_uri
                except Exception as archive_err:
                    logger.warning("Failed to archive raw response for %s: %s", result.platform, archive_err)
                finally:
                    # Raw payload can be large; release it before DB batching.
                    result.parsed.raw_response = {}
        
        # Cloud Tasks + CloudTaskExecutor already handle retry policy.
        # Keep in-handler DB attempts to 1 to avoid retry multiplication.
        max_attempts = 1
        for attempt in range(max_attempts):
            assets_to_download = []
            try:
                async with get_db_connection() as conn:
                    await set_rls_user(conn, user_uuid)
                    pass
                    
                    # Prepare batch data
                    platform_calls_batch = []
                    all_content_items = []
                    items_with_rank = []  # List of (item, rank)
                    rank = 0
                    
                    for result in collected_results:
                        slug = result.platform
                        
                        # Collect platform call
                        platform_calls_batch.append({
                            "search_id": search_id,
                            "platform": slug,
                            "request_params": result.request_params,
                            "success": result.success,
                            "http_status": result.http_status,
                            "error": result.error,
                            "duration_ms": result.duration_ms,
                            "next_cursor": result.parsed.next_cursor if result.parsed else None,
                            "response_gcs_uri": raw_uris_by_platform.get(slug),
                            "response_meta": result.parsed.response_meta if result.parsed else {},
                        })
                        
                        # Collect items
                        if result.success and result.parsed:
                            for item in result.parsed.items:
                                rank += 1
                                all_content_items.append(item)
                                items_with_rank.append((item, rank))
                    
                    # Batch Operations
                    
                    # 1. Insert platform calls
                    if platform_calls_batch:
                        await queries.insert_platform_calls_batch(conn, platform_calls_batch)
                    
                    # 2. Upsert content items
                    # Returns map: (platform, external_id) -> (content_item_id, was_inserted)
                    item_id_map = await queries.upsert_content_items_batch(conn, all_content_items)
                    
                    # 3. Prepare search results and media assets
                    search_results_batch = []
                    media_assets_batch = []
                    
                    for item, item_rank in items_with_rank:
                        key = (item.platform, item.external_id)
                        if key not in item_id_map:
                            continue
                            
                        content_item_id, was_inserted = item_id_map[key]
                        
                        search_results_batch.append({
                            "search_id": search_id,
                            "content_item_id": content_item_id,
                            "platform": item.platform,
                            "rank": item_rank,
                        })
                        
                        # Only insert assets if item was newly inserted
                        if was_inserted:
                            # Deterministic Content ID (re-calculate to ensure seed match)
                            det_content_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{item.platform}:{item.external_id}"))
                            
                            for media_url in item.media_urls:
                                # Deterministic Asset ID
                                asset_seed = f"{det_content_id}:{media_url.asset_type.value}:{media_url.source_url}"
                                asset_id = uuid.uuid5(uuid.NAMESPACE_URL, asset_seed)
                                media_assets_batch.append({
                                    "id": asset_id,
                                    "content_item_id": content_item_id,
                                    "asset_type": media_url.asset_type.value,
                                    "source_url": media_url.source_url,
                                    "source_url_list": media_url.source_url_list,
                                })
                                assets_to_download.append({
                                    "id": str(asset_id),
                                    "platform": item.platform,
                                    "external_id": item.external_id,
                                })

                    # 4. Insert search results and media assets
                    if search_results_batch:
                        await queries.insert_search_results_batch(conn, search_results_batch)
                    
                    if media_assets_batch:
                        await queries.insert_media_assets_batch(conn, media_assets_batch)
                    
                    # Update status to completed
                    await queries.update_search_status(conn, search_id, "completed")
                    await conn.commit()
                    logger.info(f"Saved search {search_id} with {rank} results (batch mode)")
                break
            except Exception:
                raise

        # ========== FINISH STREAMING ==========
        # Push done event - frontend stops loading here
        await r.xadd(
            stream_key,
            {"data": json.dumps({"type": "done"})},
            maxlen=stream_maxlen,
            approximate=True,
        )
        await r.expire(stream_key, settings.REDIS_STREAM_TTL_S_SEARCH)
        
        # ========== FIRE-AND-FORGET BACKGROUND TASKS ==========
        # GCS uploads handled via Cloud Tasks above
        
        # Media downloads: enqueue in batches to reduce DB claim/finalize query pressure.
        if assets_to_download:
            batch_size = max(1, int(getattr(settings, "MEDIA_DOWNLOAD_ENQUEUE_BATCH_SIZE", 50)))
            dispatched_at = time.time()
            enqueue_payloads = [
                {
                    "asset_id": str(asset_info["id"]),
                    "platform": asset_info["platform"],
                    "external_id": asset_info["external_id"],
                    "attempt_no": int(asset_info.get("attempt_no", 0) or 0),
                    "dispatched_at": dispatched_at,
                }
                for asset_info in assets_to_download
            ]
            for payload in enqueue_payloads:
                capture_event(
                    distinct_id="system:media_download",
                    event="media_download_dispatched",
                    properties={
                        "asset_id": payload["asset_id"],
                        "platform": payload["platform"],
                        "priority": False,
                        "attempt_no": payload["attempt_no"],
                        "dispatched_at": payload["dispatched_at"],
                        "source": "search_worker",
                    },
                )
            logger.debug(
                "Dispatching %s media download tasks to Cloud Tasks in batches of %s...",
                len(enqueue_payloads),
                batch_size,
            )
            for idx in range(0, len(enqueue_payloads), batch_size):
                await cloud_tasks.create_http_task(
                    queue_name=settings.QUEUE_MEDIA_DOWNLOAD,
                    relative_uri="/v1/tasks/media/download",
                    payload=enqueue_payloads[idx: idx + batch_size],
                )
        
    except Exception as e:
        # If the DB gate is saturated/unavailable, raise so Cloud Tasks can retry with backoff
        # (and local runners can surface the error instead of silently "failing").
        if isinstance(e, HTTPException) and e.status_code in (429, 503):
            detail = str(getattr(e, "detail", "") or "")
            if "Database is busy" in detail or "Database gate" in detail:
                raise

        logger.error(f"Search worker failed for {search_id}: {e}", exc_info=True)
        # Update status to failed
        try:
            async with get_db_connection() as conn:
                await set_rls_user(conn, user_uuid)
                await queries.update_search_status(conn, search_id, "failed")
                await conn.commit()
        except Exception as db_err:
            logger.error(f"Failed to update search status to failed: {db_err}")
        
        # Try to push error to Redis (may already be closed)
        try:
            await r.xadd(
                stream_key,
                {"data": json.dumps({"type": "error", "error": str(e)})},
                maxlen=stream_maxlen,
                approximate=True,
            )
            await r.expire(stream_key, settings.REDIS_STREAM_TTL_S_SEARCH)
            
            # Telemetry: Search Failed
            total_duration_ms = int((time.time() - start_time) * 1000)
            capture_event(
                distinct_id=str(user_uuid),
                event="search_completed",
                properties={
                    "search_id": str(search_id),
                    "duration_ms": total_duration_ms,
                    "total_duration_ms": total_duration_ms + queue_duration_ms,
                    "queue_duration_ms": queue_duration_ms,
                    "success": False,
                    "error": str(e),
                }
            )
        except Exception:
            pass


@trace_span("search.load_more_worker")
async def load_more_worker(
    search_id: UUID,
    user_uuid: UUID,
    query: str,
    platform_cursors: dict,
    redis_client: redis.Redis,
):
    """
    Background worker for "load more" pagination.
    Same pattern as search_worker but with cursors.
    
    platform_cursors = {
        "tiktok_keyword": {"cursor": 30},
        "youtube": {"continuationToken": "abc..."},
        ...
    }
    """
    settings = get_settings()
    r = redis_client
    stream_key = f"search:{search_id}:more:stream"
    stream_maxlen = settings.REDIS_STREAM_MAXLEN_SEARCH_MORE
    
    # Clear old stream messages from previous load more requests
    # This prevents the frontend from seeing stale "done" messages
    await r.delete(stream_key)
    
    collected_results: List[PlatformCallResult] = []
    
    try:
        # Push start event
        await r.xadd(
            stream_key,
            {"data": json.dumps({
                "type": "start",
                "platforms": [normalize_platform_slug(slug) for slug in platform_cursors.keys()],
                "search_id": str(search_id),
            })},
            maxlen=stream_maxlen,
            approximate=True,
        )
        
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            # Create all platform tasks with cursors merged into params
            tasks = [
                call_platform(client, slug, query, cursor_params)
                for slug, cursor_params in platform_cursors.items()
            ]
            
            # Process as they complete
            for coro in asyncio.as_completed(tasks):
                result: PlatformCallResult = await coro
                collected_results.append(result)
                
                # Transform and push to Redis
                event_data = transform_result_to_stream_item(result)
                await r.xadd(
                    stream_key,
                    {"data": json.dumps(event_data, default=str)},
                    maxlen=stream_maxlen,
                    approximate=True,
                )
        
        # ========== DB WORK ==========
        assets_to_download = []
        raw_uris_by_platform: dict[str, str] = {}

        for result in collected_results:
            if result.success and result.parsed:
                now = datetime.utcnow()
                gcs_key = f"raw/{result.platform}/{now.year}/{now.month:02d}/{now.day:02d}/{search_id}.json.gz"
                try:
                    gcs_uri = await upload_raw_json_gz(
                        platform=result.platform,
                        search_id=search_id,
                        raw_json=result.parsed.raw_response,
                        key_override=gcs_key,
                    )
                    if gcs_uri:
                        raw_uris_by_platform[result.platform] = gcs_uri
                except Exception as archive_err:
                    logger.warning("Failed to archive raw response for %s: %s", result.platform, archive_err)
                finally:
                    result.parsed.raw_response = {}

        # Cloud Tasks + CloudTaskExecutor already handle retry policy.
        # Keep in-handler DB attempts to 1 to avoid retry multiplication.
        max_attempts = 1
        for attempt in range(max_attempts):
            assets_to_download = []
            try:
                async with get_db_connection() as conn:
                    await set_rls_user(conn, user_uuid)
                    
                    # Get current max rank for this search
                    rank_result = await conn.execute(
                        text("SELECT COALESCE(MAX(rank), 0) FROM search_results WHERE search_id = :search_id"),
                        {"search_id": search_id}
                    )
                    current_max_rank = rank_result.scalar() or 0
                    
                    # Prepare batch data
                    platform_calls_batch = []
                    all_content_items = []
                    items_with_rank = []
                    rank = current_max_rank
                    
                    for result in collected_results:
                        slug = result.platform
                        
                        # Collect platform call (new call with updated cursor)
                        platform_calls_batch.append({
                            "search_id": search_id,
                            "platform": slug,
                            "request_params": result.request_params,
                            "success": result.success,
                            "http_status": result.http_status,
                            "error": result.error,
                            "duration_ms": result.duration_ms,
                            "next_cursor": result.parsed.next_cursor if result.parsed else None,
                            "response_gcs_uri": raw_uris_by_platform.get(slug),
                            "response_meta": result.parsed.response_meta if result.parsed else {},
                        })
                        
                        # Collect items
                        if result.success and result.parsed:
                            for item in result.parsed.items:
                                rank += 1
                                all_content_items.append(item)
                                items_with_rank.append((item, rank))
                    
                    # Batch Operations
                    if platform_calls_batch:
                        await queries.insert_platform_calls_batch(conn, platform_calls_batch)
                    
                    item_id_map = await queries.upsert_content_items_batch(conn, all_content_items)
                    
                    search_results_batch = []
                    media_assets_batch = []
                    
                    for item, item_rank in items_with_rank:
                        key = (item.platform, item.external_id)
                        if key not in item_id_map:
                            continue
                            
                        content_item_id, was_inserted = item_id_map[key]
                        
                        search_results_batch.append({
                            "search_id": search_id,
                            "content_item_id": content_item_id,
                            "platform": item.platform,
                            "rank": item_rank,
                        })
                        
                        if was_inserted:
                            det_content_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{item.platform}:{item.external_id}"))
                            
                            for media_url in item.media_urls:
                                asset_seed = f"{det_content_id}:{media_url.asset_type.value}:{media_url.source_url}"
                                asset_id = uuid.uuid5(uuid.NAMESPACE_URL, asset_seed)
                                media_assets_batch.append({
                                    "id": asset_id,
                                    "content_item_id": content_item_id,
                                    "asset_type": media_url.asset_type.value,
                                    "source_url": media_url.source_url,
                                    "source_url_list": media_url.source_url_list,
                                })
                                assets_to_download.append({
                                    "id": str(asset_id),
                                    "platform": item.platform,
                                    "external_id": item.external_id,
                                })

                    if search_results_batch:
                        await queries.insert_search_results_batch(conn, search_results_batch)
                    
                    if media_assets_batch:
                        await queries.insert_media_assets_batch(conn, media_assets_batch)
                    
                    await conn.commit()
                    logger.info(f"Load more for search {search_id}: added {len(items_with_rank)} results")
                break
            except Exception:
                raise

        # ========== FINISH STREAMING ==========
        await r.xadd(
            stream_key,
            {"data": json.dumps({"type": "done"})},
            maxlen=stream_maxlen,
            approximate=True,
        )
        await r.expire(stream_key, settings.REDIS_STREAM_TTL_S_SEARCH)
        
        # ========== FIRE-AND-FORGET BACKGROUND TASKS ==========
        if assets_to_download:
            batch_size = max(1, int(getattr(settings, "MEDIA_DOWNLOAD_ENQUEUE_BATCH_SIZE", 50)))
            dispatched_at = time.time()
            enqueue_payloads = [
                {
                    "asset_id": str(asset_info["id"]),
                    "platform": asset_info["platform"],
                    "external_id": asset_info["external_id"],
                    "attempt_no": int(asset_info.get("attempt_no", 0) or 0),
                    "dispatched_at": dispatched_at,
                }
                for asset_info in assets_to_download
            ]
            for payload in enqueue_payloads:
                capture_event(
                    distinct_id="system:media_download",
                    event="media_download_dispatched",
                    properties={
                        "asset_id": payload["asset_id"],
                        "platform": payload["platform"],
                        "priority": False,
                        "attempt_no": payload["attempt_no"],
                        "dispatched_at": payload["dispatched_at"],
                        "source": "load_more_worker",
                    },
                )
            logger.debug(
                "Dispatching %s media download tasks for load_more in batches of %s...",
                len(enqueue_payloads),
                batch_size,
            )
            for idx in range(0, len(enqueue_payloads), batch_size):
                await cloud_tasks.create_http_task(
                    queue_name=settings.QUEUE_MEDIA_DOWNLOAD,
                    relative_uri="/v1/tasks/media/download",
                    payload=enqueue_payloads[idx: idx + batch_size],
                )
        
    except Exception as e:
        if isinstance(e, HTTPException) and e.status_code in (429, 503):
            detail = str(getattr(e, "detail", "") or "")
            if "Database is busy" in detail or "Database gate" in detail:
                raise

        logger.error(f"Load more worker failed for {search_id}: {e}", exc_info=True)
        
        try:
            await r.xadd(
                stream_key,
                {"data": json.dumps({"type": "error", "error": str(e)})},
                maxlen=stream_maxlen,
                approximate=True,
            )
            await r.expire(stream_key, settings.REDIS_STREAM_TTL_S_SEARCH)
        except Exception:
            pass


# --- Redis Dependency ---

async def get_redis(request: Request):
    """Get Redis client instance."""
    try:
        client = get_app_redis(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    yield client


# --- Endpoints ---

@router.post("/search")
@trace_span("search.create_search")
async def create_search(
    request: SearchRequest,
    user: dict = Depends(get_current_user),
):
    """
    Create a new search.
    
    Returns search_id immediately, runs search in background.
    Frontend should connect to /search/{id}/stream for results.
    """
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    # Validate platforms
    for slug in request.inputs.keys():
        if slug not in PLATFORM_ADAPTERS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown platform: {slug}. Available: {list(PLATFORM_ADAPTERS.keys())}"
            )
    
    # Check and charge credits
    from app.services.credit_tracker import credit_tracker
    from sqlalchemy import text
    
    # Check and record credits + create search in one connection
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        result = await conn.execute(
            text("SELECT current_period_start, timezone FROM users WHERE id = :id"),
            {"id": user_uuid}
        )
        row = result.fetchone()
        period_start = row[0] if row else None
        timezone = row[1] if row and row[1] else "UTC"

        credit_result = await credit_tracker.check(
            user_id=user_uuid,
            role=user.get("role", "free"),
            feature="search_query",
            current_period_start=period_start,
            record=True,
            context={"platforms": list(request.inputs.keys())},
            conn=conn,
        )
        if not credit_result["allowed"]:
            raise HTTPException(status_code=402, detail="Credit limit exceeded")
        search_id = await queries.insert_search(
            conn=conn,
            user_id=user_uuid,
            query=request.query,
            inputs=request.inputs,
            mode="live",
            status="running",
        )
        # analytics outbox removed
        await conn.commit()

    # Spawn background worker via Cloud Tasks
    settings = get_settings()
    await cloud_tasks.create_http_task(
        queue_name=settings.QUEUE_SEARCH_WORKER,
        relative_uri="/v1/tasks/search/run",
        payload={
            "search_id": str(search_id),
            "user_uuid": str(user_uuid),
            "query": request.query,
            "query": request.query,
            "inputs": request.inputs,
            "dispatched_at": time.time(),
        },
    )
    
    return {"search_id": str(search_id)}



@router.get("/search/{search_id}/stream")
@trace_span("search.stream_search")
async def stream_search(
    search_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
    last_event_id: str | None = Header(None, alias="Last-Event-ID"),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    SSE endpoint to stream search results from Redis.
    
    If search is already completed, returns JSON with results from DB.
    If search is running, streams from Redis.
    """
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    # Verify user owns this search and get status
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        search = await queries.get_search_by_id(conn, search_id)
        
        if not search:
            raise HTTPException(status_code=404, detail="Search not found")
        
        # If already completed, return results from DB
        if search["status"] == "completed":
            results = await queries.get_search_results_with_content(conn, search_id)
            # Single-hop requirement: sign stored assets directly in the response.
            uris_to_sign: list[str] = []
            for item in results:
                for a in item.get("assets", []) or []:
                    if should_sign_asset(a):
                        uris_to_sign.append(a["gcs_uri"])

            signed_cache: dict[str, str] = {}
            try:
                signed_cache = await bulk_sign_gcs_uris(uris_to_sign, expiration_seconds=3600, max_concurrency=25)
            except Exception as e:
                logger.warning("Bulk signing failed for search_id=%s: %s", search_id, e)

            for item in results:
                for a in item.get("assets", []) or []:
                    if should_sign_asset(a):
                        a["source_url"] = signed_cache.get(a["gcs_uri"], a.get("source_url"))
            return {
                "status": "completed",
                "results": results,
            }
        
        if search["status"] == "failed":
            return {
                "status": "failed",
                "error": "Search failed",
            }
    
    # Status is 'running' - stream from Redis
    stream_key = f"search:{search_id}:stream"
    
    hub = getattr(request.app.state, "stream_hub", None)

    async def event_generator():
        async def catch_up_from_redis(last_id: str):
            nonlocal last_sent_id
            cur = last_id or "0-0"
            while True:
                streams = await redis_client.xread({stream_key: cur}, count=200, block=0)
                if not streams:
                    return
                _, messages = streams[0]
                if not messages:
                    return
                for msg_id, data_map in messages:
                    payload_str = data_map.get("data")
                    cur = msg_id
                    last_sent_id = msg_id
                    if payload_str is None:
                        continue
                    yield {
                        "id": msg_id,
                        "event": "message",
                        "data": payload_str,
                    }
                    await asyncio.sleep(0)
                    if _is_terminal_payload(payload_str):
                        return
                if len(messages) < 200:
                    return

        if hub is None:
            logger.warning(
                "Stream hub missing; SSE will use per-connection Redis XREAD. search_id=%s",
                search_id,
            )
            last_id = last_event_id or "0-0"
            try:
                while True:
                    if await request.is_disconnected():
                        return
                    streams = await redis_client.xread(
                        {stream_key: last_id},
                        count=50,
                        block=10000,
                    )
                    if not streams:
                        yield {"event": "ping", "data": ""}
                        continue
                    for _, messages in streams:
                        for msg_id, data_map in messages:
                            last_id = msg_id
                            payload_str = data_map.get("data")
                            yield {
                                "id": msg_id,
                                "event": "message",
                                "data": payload_str,
                            }
                            if _is_terminal_payload(payload_str):
                                return
            except asyncio.CancelledError:
                pass
            return

        queue = await hub.subscribe(stream_key)
        last_sent_id = last_event_id or "0-0"
        try:
            async for ev in catch_up_from_redis(last_sent_id):
                yield ev
                if _is_terminal_payload(ev.get("data")):
                    return

            while True:
                try:
                    msg_id, payload_str = await asyncio.wait_for(queue.get(), timeout=10)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
                    async for ev in catch_up_from_redis(last_sent_id):
                        yield ev
                        if _is_terminal_payload(ev.get("data")):
                            return
                    continue
                if not payload_str:
                    continue
                if not stream_id_gt(msg_id, last_sent_id):
                    continue
                last_sent_id = msg_id
                yield {
                    "id": msg_id,
                    "event": "message",
                    "data": payload_str,
                }
                if _is_terminal_payload(payload_str):
                    return
        except asyncio.CancelledError:
            pass
        finally:
            await hub.unsubscribe(stream_key, queue)
    
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return EventSourceResponse(event_generator(), headers=headers)


@router.post("/search/{search_id}/more")
@trace_span("search.load_more")
async def load_more(
    search_id: UUID,
    user: dict = Depends(get_current_user),
    payload: LoadMoreRequest | None = None,
):
    """
    Load more results for an existing search using pagination cursors.
    
    Returns search_id immediately, runs load_more in background.
    Frontend should connect to /search/{id}/more/stream for results.
    """
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        # Get search with cursors
        search_data = await queries.get_search_with_cursors(conn, search_id)
        
        if not search_data:
            raise HTTPException(status_code=404, detail="Search not found")
        
        cursors = search_data.get("cursors", {})
        
        # Filter out platforms without cursors and Instagram (no pagination support)
        platform_cursors = {}
        original_inputs = search_data.get("inputs", {})
        input_overrides = (payload.inputs if payload and payload.inputs else {}) or {}
        
        for platform, cursor in cursors.items():
            if platform == "instagram_reels":
                if platform in input_overrides or platform in original_inputs:
                    params = {**original_inputs.get(platform, {}), **input_overrides.get(platform, {})}
                    platform_cursors[platform] = params
                continue
            if cursor and platform in original_inputs:
                # Merge original params with cursor
                params = {**original_inputs[platform], **input_overrides.get(platform, {}), **cursor}
                platform_cursors[platform] = params

        if "instagram_reels" not in platform_cursors and ("instagram_reels" in input_overrides or "instagram_reels" in original_inputs):
            params = {**original_inputs.get("instagram_reels", {}), **input_overrides.get("instagram_reels", {})}
            platform_cursors["instagram_reels"] = params
    
        if not platform_cursors:
            raise HTTPException(
                status_code=400, 
                detail="No more results available (no platforms have pagination cursors)"
            )

        # Check and charge credits
        from app.services.credit_tracker import credit_tracker
        from sqlalchemy import text
        
        result = await conn.execute(
            text("SELECT current_period_start, timezone FROM users WHERE id = :id"),
            {"id": user_uuid}
        )
        row = result.fetchone()
        period_start = row[0] if row else None
        timezone = row[1] if row and row[1] else "UTC"

        credit_result = await credit_tracker.check(
            user_id=user_uuid,
            role=user.get("role", "free"),
            feature="search_query",
            current_period_start=period_start,
            record=True,
            context={"search_id": str(search_id), "platforms": list(platform_cursors.keys()), "action": "load_more"},
            conn=conn,
        )
        if not credit_result["allowed"]:
            raise HTTPException(status_code=402, detail="Credit limit exceeded")
        from app.db.queries import streaks as streak_queries
        await streak_queries.record_activity(conn, user_uuid, "search", timezone=timezone)
        # analytics outbox removed
        await conn.commit()
    
    # Spawn background worker via Cloud Tasks
    settings = get_settings()
    await cloud_tasks.create_http_task(
        queue_name=settings.QUEUE_SEARCH_WORKER,
        relative_uri="/v1/tasks/search/load_more",
        payload={
            "search_id": str(search_id),
            "user_uuid": str(user_uuid),
            "query": search_data["query"],
            "platform_cursors": platform_cursors,
        },
    )
    
    return {"search_id": str(search_id), "platforms": list(platform_cursors.keys())}


@router.get("/search/{search_id}/more/stream")
@trace_span("search.stream_load_more")
async def stream_load_more(
    search_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
    last_event_id: str | None = Header(None, alias="Last-Event-ID"),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    SSE endpoint to stream load_more results from Redis.
    Same pattern as /search/{id}/stream but uses different stream key.
    """
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    # Verify user owns this search
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        search = await queries.get_search_by_id(conn, search_id)
        
        if not search:
            raise HTTPException(status_code=404, detail="Search not found")
    
    # Stream from Redis
    stream_key = f"search:{search_id}:more:stream"
    hub = getattr(request.app.state, "stream_hub", None)
    
    async def event_generator():
        async def catch_up_from_redis(last_id: str):
            nonlocal last_sent_id
            cur = last_id or "0-0"
            while True:
                streams = await redis_client.xread({stream_key: cur}, count=200, block=0)
                if not streams:
                    return
                _, messages = streams[0]
                if not messages:
                    return
                for msg_id, data_map in messages:
                    payload_str = data_map.get("data")
                    cur = msg_id
                    last_sent_id = msg_id
                    if payload_str is None:
                        continue
                    yield {
                        "id": msg_id,
                        "event": "message",
                        "data": payload_str,
                    }
                    await asyncio.sleep(0)
                    if _is_terminal_payload(payload_str):
                        return
                if len(messages) < 200:
                    return

        if hub is None:
            last_id = last_event_id or "0-0"
            try:
                while True:
                    if await request.is_disconnected():
                        return
                    streams = await redis_client.xread(
                        {stream_key: last_id},
                        count=50,
                        block=10000,
                    )
                    if not streams:
                        yield {"event": "ping", "data": ""}
                        continue
                    for _, messages in streams:
                        for msg_id, data_map in messages:
                            last_id = msg_id
                            payload_str = data_map.get("data")
                            yield {
                                "id": msg_id,
                                "event": "message",
                                "data": payload_str,
                            }
                            await asyncio.sleep(0)
                            if _is_terminal_payload(payload_str):
                                return
            except asyncio.CancelledError:
                pass
            return

        queue = await hub.subscribe(stream_key)
        last_sent_id = last_event_id or "0-0"
        try:
            async for ev in catch_up_from_redis(last_sent_id):
                yield ev
                if _is_terminal_payload(ev.get("data")):
                    return

            while True:
                try:
                    msg_id, payload_str = await asyncio.wait_for(queue.get(), timeout=10)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
                    async for ev in catch_up_from_redis(last_sent_id):
                        yield ev
                        if _is_terminal_payload(ev.get("data")):
                            return
                    continue
                if not payload_str:
                    continue
                if not stream_id_gt(msg_id, last_sent_id):
                    continue
                last_sent_id = msg_id
                yield {
                    "id": msg_id,
                    "event": "message",
                    "data": payload_str,
                }
                await asyncio.sleep(0)
                if _is_terminal_payload(payload_str):
                    return
        except asyncio.CancelledError:
            pass
        finally:
            await hub.unsubscribe(stream_key, queue)
    
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return EventSourceResponse(event_generator(), headers=headers)
