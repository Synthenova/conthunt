"""Search API endpoint - POST /v1/search."""
import asyncio
import time
from typing import List
from uuid import UUID
import traceback
from dataclasses import asdict

import httpx
import json
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.core import get_settings, logger
from app.db import get_db_connection, get_or_create_user, set_rls_user, queries
from app.platforms import (
    PLATFORM_ADAPTERS,
    get_adapter,
    PlatformCallResult,
    ParsedPlatformResponse,
)
from app.storage import upload_raw_json_gz
from app.media import download_assets_batch
from app.schemas import (
    SearchRequest,
    SearchResponse,
    PlatformResult,
    ContentItemResponse,
    AssetResponse,
    ResultItem,
)

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
        print(traceback.format_exc())
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Platform {slug} error: {e}")
        return PlatformCallResult(
            platform=slug,
            success=False,
            error=str(e),
            duration_ms=duration_ms,
            request_params=request_params,
        )


async def save_search_background(
    user_uuid: UUID,
    query: str,
    inputs: dict,
    platform_results: List[PlatformCallResult],
    new_media_assets: List[dict] = None
):
    """Background task to save search history and results."""
    try:
        async with get_db_connection() as conn:
            # Set RLS context
            await set_rls_user(conn, user_uuid)
            
            # Insert search
            search_id = await queries.insert_search(
                conn=conn,
                user_id=user_uuid,
                query=query,
                inputs=inputs,
                mode="live",
            )
            
            rank = 0
            assets_to_download = []
            
            for result in platform_results:
                slug = result.platform
                
                # Upload raw response to GCS if successful
                response_gcs_uri = None
                if result.success and result.parsed:
                    response_gcs_uri = await upload_raw_json_gz(
                        platform=slug,
                        search_id=search_id,
                        raw_json=result.parsed.raw_response,
                    )
                
                # Insert platform call record
                await queries.insert_platform_call(
                    conn=conn,
                    search_id=search_id,
                    platform=slug,
                    request_params=result.request_params,
                    success=result.success,
                    http_status=result.http_status,
                    error=result.error,
                    duration_ms=result.duration_ms,
                    next_cursor=result.parsed.next_cursor if result.parsed else None,
                    response_gcs_uri=response_gcs_uri,
                    response_meta=result.parsed.response_meta if result.parsed else {},
                )
                
                # Process items if successful
                if result.success and result.parsed:
                    for item in result.parsed.items:
                        rank += 1
                        
                        # Upsert content item
                        content_id, was_inserted = await queries.upsert_content_item(conn, item)
                        
                        # Insert search result link
                        await queries.insert_search_result(
                            conn=conn,
                            search_id=search_id,
                            content_item_id=content_id,
                            platform=item.platform,
                            rank=rank,
                        )
                        
                        # Only create media assets for newly inserted content
                        if was_inserted:
                            for media_url in item.media_urls:
                                asset_id = await queries.insert_media_asset(
                                    conn=conn,
                                    content_item_id=content_id,
                                    media_url=media_url,
                                )
                                # Track for download
                                assets_to_download.append({
                                    "id": asset_id,
                                    "platform": item.platform,
                                    "external_id": item.external_id,
                                })

            await conn.commit()
            logger.info(f"Saved search {search_id} with {rank} results")

            # Trigger media downloads
            if assets_to_download:
                # We can call the download function directly as we are already in a background task
                # logic here, or spawn another task if we want.
                # Since the download function is async, we can just await it or create_task
                await download_assets_batch(assets_to_download)

    except Exception as e:
        logger.error(f"Failed to save search history: {e}")


@router.post("/search", response_class=EventSourceResponse)
async def create_search(
    request: SearchRequest,
    user: dict = Depends(get_current_user),
):
    """
    Execute a multi-platform search with Streaming Response (SSE).
    Results are yielded as they arrive. Database operations happen in background.
    """
    settings = get_settings()
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
    
    # Get user UUID (needed for background task)
    async with get_db_connection() as conn:
         user_uuid, _ = await get_or_create_user(conn, firebase_uid)

    async def event_generator():
        # Clean inputs
        platform_tasks = []
        collected_results: List[PlatformCallResult] = []
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Create tasks
            for slug, params in request.inputs.items():
                platform_tasks.append(call_platform(client, slug, request.query, params))
            
            # Yield initial event
            yield {
                "event": "start",
                "data": json.dumps({"message": f"Starting search on {len(platform_tasks)} platforms"})
            }
            
            # Use as_completed to yield results as they finish
            for task in asyncio.as_completed(platform_tasks):
                result: PlatformCallResult = await task
                collected_results.append(result)
                
                # Transform to lightweight response
                
                # We need to map the raw NormalizedItem to the expected schema (ResultItem)
                # This matches what the frontend expects (nested content_item and assets)
                items_data = []
                if result.parsed:
                    for item in result.parsed.items:
                        # Construct assets list
                        assets_data = []
                        for media in item.media_urls:
                            # We don't have DB IDs yet, so we use a placeholder or None
                            # The frontend keys off content_item.id usually, but assets might need IDs
                            # Let's generate a temporary ID if needed, or just leave it empty if frontend tolerates it
                            # Actually, frontend likely needs some unique key. But since this is a stream, 
                            # we can't give real DB IDs.
                            assets_data.append({
                                "id": None, # Will be ignored or handled by frontend keys
                                "asset_type": media.asset_type.value,
                                "status": "pending",
                                "source_url": media.source_url,
                                "gcs_uri": None
                            })

                        items_data.append({
                            "rank": 0, # Not relevant for stream
                            "content_item": {
                                "id": None, # No DB ID yet
                                "platform": item.platform,
                                "external_id": item.external_id,
                                "content_type": item.content_type,
                                "canonical_url": item.canonical_url,
                                "title": item.title,
                                "primary_text": item.primary_text,
                                "published_at": item.published_at,
                                "creator_handle": item.creator_handle,
                                "metrics": item.metrics,
                            },
                            "assets": assets_data
                        })

                data = {
                    "platform": result.platform,
                    "success": result.success,
                    "duration_ms": result.duration_ms,
                    "count": len(result.parsed.items) if result.parsed else 0,
                    "items": items_data,
                    "error": result.error
                }
                
                yield {
                    "event": "platform_result",
                    "data": json.dumps(data, default=str)
                }

        # Verification: All done
        yield {
            "event": "done",
            "data": json.dumps({"message": "All platforms finished"})
        }
        
        # Spawn background task to save to DB
        # We use asyncio.create_task to ensure it runs after the generator finishes/returns
        asyncio.create_task(save_search_background(
            user_uuid=user_uuid,
            query=request.query,
            inputs=request.inputs,
            platform_results=collected_results
        ))

    return EventSourceResponse(event_generator())
