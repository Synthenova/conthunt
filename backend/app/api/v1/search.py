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
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request

from app.auth import get_current_user
from app.core import get_settings, logger
from app.db import get_db_connection, get_or_create_user, set_rls_user, queries
from app.services.user_cache import get_cached_user_uuid
from app.platforms import (
    PLATFORM_ADAPTERS,
    get_adapter,
    PlatformCallResult,
)
from app.storage import upload_raw_json_gz
from app.media import download_assets_batch
from app.schemas import SearchRequest
from app.services.cloud_tasks import cloud_tasks

router = APIRouter()


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
        "platform": result.platform,
        "success": result.success,
        "duration_ms": result.duration_ms,
        "count": len(result.parsed.items) if result.parsed else 0,
        "items": items_data,
        "error": result.error,
        "next_cursor": result.parsed.next_cursor if result.parsed else None,
    }


async def search_worker(
    search_id: UUID,
    user_uuid: UUID,
    query: str,
    inputs: dict,
):
    """
    Background worker that:
    1. Fetches all platforms and pushes results to Redis
    2. Immediately pushes "done" to Redis (frontend stops loading)
    3. Saves to DB and updates status
    4. Fire-and-forget: uploads and media downloads
    """
    settings = get_settings()
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    stream_key = f"search:{search_id}:stream"
    
    collected_results: List[PlatformCallResult] = []
    
    try:
        # Push start event
        await r.xadd(stream_key, {"data": json.dumps({
            "type": "start", 
            "platforms": list(inputs.keys()),
            "search_id": str(search_id),
        })})
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
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
        await r.close()
        
        # ========== FIRE-AND-FORGET BACKGROUND TASKS ==========
        # GCS uploads handled via Cloud Tasks above
        
        # Media downloads: Fan-out via Cloud Tasks
        if assets_to_download:
            logger.info(f"Dispatching {len(assets_to_download)} media download tasks to Cloud Tasks...")
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
            r2 = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await r2.xadd(stream_key, {"data": json.dumps({"type": "error", "error": str(e)})})
            await r2.expire(stream_key, 300)
            await r2.close()
        except:
            pass


# --- Redis Dependency ---

async def get_redis():
    """Get Redis client instance."""
    settings = get_settings()
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()


# --- Endpoints ---

@router.post("/search")
async def create_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """
    Create a new search.
    
    Returns search_id immediately, runs search in background.
    Frontend should connect to /search/{id}/stream for results.
    """
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    # Validate platforms
    for slug in request.inputs.keys():
        if slug not in PLATFORM_ADAPTERS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown platform: {slug}. Available: {list(PLATFORM_ADAPTERS.keys())}"
            )
    
    # Get user UUID and create search entry
    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, firebase_uid)
        await set_rls_user(conn, user_uuid)
        
        search_id = await queries.insert_search(
            conn=conn,
            user_id=user_uuid,
            query=request.query,
            inputs=request.inputs,
            mode="live",
            status="running",
        )
        await conn.commit()
    
    # Spawn background worker
    background_tasks.add_task(
        search_worker,
        search_id=search_id,
        user_uuid=user_uuid,
        query=request.query,
        inputs=request.inputs,
    )
    
    return {"search_id": str(search_id)}


@router.get("/search/{search_id}/stream")
async def stream_search(
    search_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    SSE endpoint to stream search results from Redis.
    
    If search is already completed, returns JSON with results from DB.
    If search is running, streams from Redis.
    """
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    # Verify user owns this search and get status
    async with get_db_connection() as conn:
        user_uuid = await get_cached_user_uuid(conn, firebase_uid)
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
