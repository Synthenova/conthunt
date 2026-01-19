"""Search API endpoint - POST /v1/search with Redis streaming."""
import asyncio
import base64
import gzip
import time
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
from app.core.telemetry import trace_span
from app.db import get_db_connection, set_rls_user, queries

from app.platforms import (
    PLATFORM_ADAPTERS,
    get_adapter,
    PlatformCallResult,
)
from app.platforms.registry import normalize_platform_slug
from app.storage import upload_raw_json_gz
from app.media import download_assets_batch
from app.schemas import SearchRequest
from app.services.cloud_tasks import cloud_tasks
from app.realtime.stream_hub import stream_id_gt

router = APIRouter()


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
    redis_client: redis.Redis | None = None,
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
    owns_client = False
    if r is None:
        r = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_keepalive=True,
            health_check_interval=30,
        )
        owns_client = True
    stream_key = f"search:{search_id}:stream"
    
    collected_results: List[PlatformCallResult] = []
    
    try:
        # Push start event
        await r.xadd(stream_key, {"data": json.dumps({
            "type": "start", 
            "platforms": [normalize_platform_slug(slug) for slug in inputs.keys()],
            "search_id": str(search_id),
        })})
        
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
                await r.xadd(stream_key, {"data": json.dumps(event_data, default=str)})
        
        # ========== DB WORK (happens after frontend is done) ==========
        assets_to_download = []
        upload_tasks = []  # For fire-and-forget GCS uploads
        
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
                    "response_gcs_uri": None,
                    "response_meta": result.parsed.response_meta if result.parsed else {},
                })
                
                # Queue GCS upload as task (one per platform)
                if result.success and result.parsed:
                    # Compress raw JSON to stay under Cloud Tasks' 100KB limit
                    raw_json_bytes = json.dumps(result.parsed.raw_response).encode('utf-8')
                    compressed = gzip.compress(raw_json_bytes)
                    compressed_b64 = base64.b64encode(compressed).decode('ascii')
                    
                    await cloud_tasks.create_http_task(
                        queue_name=settings.QUEUE_RAW_ARCHIVE,
                        relative_uri="/v1/tasks/raw/archive",
                        payload={
                            "platform": slug,
                            "search_id": str(search_id),
                            "raw_json_compressed": compressed_b64
                        }
                    )
                
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

        # ========== FINISH STREAMING ==========
        # Push done event - frontend stops loading here
        await r.xadd(stream_key, {"data": json.dumps({"type": "done"})})
        # Expire stream 5 minutes from now
        await r.expire(stream_key, 300)
        
        # ========== FIRE-AND-FORGET BACKGROUND TASKS ==========
        # GCS uploads handled via Cloud Tasks above
        
        # Media downloads: Fan-out via Cloud Tasks
        if assets_to_download:
            logger.debug(f"Dispatching {len(assets_to_download)} media download tasks to Cloud Tasks...")
            for asset_info in assets_to_download:
                await cloud_tasks.create_http_task(
                    queue_name=settings.QUEUE_MEDIA_DOWNLOAD,
                    relative_uri="/v1/tasks/media/download",
                    payload={
                        "asset_id": str(asset_info["id"]),
                        "platform": asset_info["platform"],
                        "external_id": asset_info["external_id"]
                    }
                )
        
    except Exception as e:
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
            await r.xadd(stream_key, {"data": json.dumps({"type": "error", "error": str(e)})})
            await r.expire(stream_key, 300)
        except Exception:
            pass
    finally:
        if owns_client:
            await r.close()


@trace_span("search.load_more_worker")
async def load_more_worker(
    search_id: UUID,
    user_uuid: UUID,
    query: str,
    platform_cursors: dict,
    redis_client: redis.Redis | None = None,
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
    owns_client = False
    if r is None:
        r = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_keepalive=True,
            health_check_interval=30,
        )
        owns_client = True
    stream_key = f"search:{search_id}:more:stream"
    
    # Clear old stream messages from previous load more requests
    # This prevents the frontend from seeing stale "done" messages
    await r.delete(stream_key)
    
    collected_results: List[PlatformCallResult] = []
    
    try:
        # Push start event
        await r.xadd(stream_key, {"data": json.dumps({
            "type": "start", 
            "platforms": [normalize_platform_slug(slug) for slug in platform_cursors.keys()],
            "search_id": str(search_id),
        })})
        
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
                await r.xadd(stream_key, {"data": json.dumps(event_data, default=str)})
        
        # ========== DB WORK ==========
        assets_to_download = []
        
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
                    "response_gcs_uri": None,
                    "response_meta": result.parsed.response_meta if result.parsed else {},
                })
                
                # Queue GCS upload as task
                if result.success and result.parsed:
                    raw_json_bytes = json.dumps(result.parsed.raw_response).encode('utf-8')
                    compressed = gzip.compress(raw_json_bytes)
                    compressed_b64 = base64.b64encode(compressed).decode('ascii')
                    
                    await cloud_tasks.create_http_task(
                        queue_name=settings.QUEUE_RAW_ARCHIVE,
                        relative_uri="/v1/tasks/raw/archive",
                        payload={
                            "platform": slug,
                            "search_id": str(search_id),
                            "raw_json_compressed": compressed_b64
                        }
                    )
                
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

        # ========== FINISH STREAMING ==========
        await r.xadd(stream_key, {"data": json.dumps({"type": "done"})})
        await r.expire(stream_key, 300)
        
        # ========== FIRE-AND-FORGET BACKGROUND TASKS ==========
        if assets_to_download:
            logger.debug(f"Dispatching {len(assets_to_download)} media download tasks for load_more...")
            for asset_info in assets_to_download:
                await cloud_tasks.create_http_task(
                    queue_name=settings.QUEUE_MEDIA_DOWNLOAD,
                    relative_uri="/v1/tasks/media/download",
                    payload={
                        "asset_id": str(asset_info["id"]),
                        "platform": asset_info["platform"],
                        "external_id": asset_info["external_id"]
                    }
                )
        
    except Exception as e:
        logger.error(f"Load more worker failed for {search_id}: {e}", exc_info=True)
        
        try:
            await r.xadd(stream_key, {"data": json.dumps({"type": "error", "error": str(e)})})
            await r.expire(stream_key, 300)
        except Exception:
            pass
    finally:
        if owns_client:
            await r.close()


# --- Redis Dependency ---

async def get_redis(request: Request):
    """Get Redis client instance."""
    client = getattr(request.app.state, "redis", None)
    if client is not None:
        yield client
        return

    settings = get_settings()
    client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_keepalive=True,
        health_check_interval=30,
    )
    try:
        yield client
    finally:
        await client.close()


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
            text("SELECT current_period_start FROM users WHERE id = :id"),
            {"id": user_uuid}
        )
        row = result.fetchone()
        period_start = row[0] if row else None

        await credit_tracker.check(
            user_id=user_uuid,
            role=user.get("role", "free"),
            feature="search_query",
            current_period_start=period_start,
            record=True,
            context={"platforms": list(request.inputs.keys())},
            conn=conn,
        )

        search_id = await queries.insert_search(
            conn=conn,
            user_id=user_uuid,
            query=request.query,
            inputs=request.inputs,
            mode="live",
            status="running",
        )
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
            "inputs": request.inputs,
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
        if hub is None:
            last_id = "0-0"
            try:
                while True:
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
                            if payload_str and '"type": "done"' in payload_str:
                                return
                            if payload_str and '"type": "error"' in payload_str:
                                return
            except asyncio.CancelledError:
                pass
            return

        queue = await hub.subscribe(stream_key)
        last_sent_id = last_event_id or "0-0"
        try:
            min_id = "-" if not last_event_id else f"({last_event_id}"
            history = await redis_client.xrange(stream_key, min=min_id, max="+")
            for msg_id, data_map in history:
                payload_str = data_map.get("data")
                if payload_str is None:
                    continue
                last_sent_id = msg_id
                yield {
                    "id": msg_id,
                    "event": "message",
                    "data": payload_str,
                }
                if payload_str and '"type": "done"' in payload_str:
                    return
                if payload_str and '"type": "error"' in payload_str:
                    return

            while True:
                try:
                    msg_id, payload_str = await asyncio.wait_for(queue.get(), timeout=10)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
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
                if payload_str and '"type": "done"' in payload_str:
                    return
                if payload_str and '"type": "error"' in payload_str:
                    return
        except asyncio.CancelledError:
            pass
        finally:
            await hub.unsubscribe(stream_key, queue)
    
    return EventSourceResponse(event_generator())


@router.post("/search/{search_id}/more")
@trace_span("search.load_more")
async def load_more(
    search_id: UUID,
    user: dict = Depends(get_current_user),
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
        
        for platform, cursor in cursors.items():
            if platform == "instagram_reels":
                continue
            if cursor and platform in original_inputs:
                # Merge original params with cursor
                params = {**original_inputs[platform], **cursor}
                platform_cursors[platform] = params
        
        if not platform_cursors:
            raise HTTPException(
                status_code=400, 
                detail="No more results available (no platforms have pagination cursors)"
            )
    
        # Check and charge credits
        from app.services.credit_tracker import credit_tracker
        from sqlalchemy import text
        
        result = await conn.execute(
            text("SELECT current_period_start FROM users WHERE id = :id"),
            {"id": user_uuid}
        )
        row = result.fetchone()
        period_start = row[0] if row else None
    
        await credit_tracker.check(
            user_id=user_uuid,
            role=user.get("role", "free"),
            feature="search_query",
            current_period_start=period_start,
            record=True,
            context={"search_id": str(search_id), "platforms": list(platform_cursors.keys()), "action": "load_more"},
            conn=conn,
        )
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
    
    async def event_generator():
        last_id = "0-0"
        
        try:
            while True:
                if await request.is_disconnected():
                    break
                
                streams = await redis_client.xread(
                    {stream_key: last_id},
                    count=50,
                    block=10000  # 10 second timeout
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
                            "data": payload_str
                        }
                        
                        # Check if done
                        if payload_str and '"type": "done"' in payload_str:
                            return
                        if payload_str and '"type": "error"' in payload_str:
                            return
        except asyncio.CancelledError:
            pass
    
    return EventSourceResponse(event_generator())
