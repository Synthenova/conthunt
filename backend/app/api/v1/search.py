"""Search API endpoint - POST /v1/search."""
import asyncio
import time
from typing import List
from uuid import UUID

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

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
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Platform {slug} error: {e}")
        return PlatformCallResult(
            platform=slug,
            success=False,
            error=str(e),
            duration_ms=duration_ms,
            request_params=request_params,
        )


@router.post("/search", response_model=SearchResponse)
async def create_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """
    Execute a multi-platform search.
    
    Calls all requested platforms concurrently, stores results,
    and schedules background media downloads.
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
    
    # Call all platforms concurrently
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        tasks = [
            call_platform(client, slug, request.query, params)
            for slug, params in request.inputs.items()
        ]
        platform_results: List[PlatformCallResult] = await asyncio.gather(*tasks)
    
    # Now do database operations in a transaction
    async with get_db_connection() as conn:
        # Get or create user
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
        
        # Set RLS context
        await set_rls_user(conn, user_uuid)
        
        # Insert search
        search_id = await queries.insert_search(
            conn=conn,
            user_id=user_uuid,
            query=request.query,
            inputs=request.inputs,
            mode="live",
        )
        
        # Process each platform result
        platforms_response = {}
        all_results = []
        new_media_assets = []  # For background download
        rank = 0
        
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
            
            # Build platform result for response
            platforms_response[slug] = PlatformResult(
                success=result.success,
                next_cursor=result.parsed.next_cursor if result.parsed else None,
                error=result.error,
                meta=result.parsed.response_meta if result.parsed else {},
                duration_ms=result.duration_ms,
                items_count=len(result.parsed.items) if result.parsed else 0,
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
                    assets = []
                    if was_inserted:
                        for media_url in item.media_urls:
                            asset_id = await queries.insert_media_asset(
                                conn=conn,
                                content_item_id=content_id,
                                media_url=media_url,
                            )
                            assets.append(AssetResponse(
                                id=asset_id,
                                asset_type=media_url.asset_type.value,
                                status="pending",
                                source_url=media_url.source_url,
                            ))
                            # Track for background download
                            new_media_assets.append({
                                "id": asset_id,
                                "platform": item.platform,
                                "external_id": item.external_id,
                            })
                    
                    # Build result item
                    all_results.append(ResultItem(
                        rank=rank,
                        content_item=ContentItemResponse(
                            id=content_id,
                            platform=item.platform,
                            external_id=item.external_id,
                            content_type=item.content_type,
                            canonical_url=item.canonical_url,
                            title=item.title,
                            primary_text=item.primary_text,
                            published_at=item.published_at,
                            creator_handle=item.creator_handle,
                            metrics=item.metrics,
                        ),
                        assets=assets,
                    ))
        
        # Commit transaction
        await conn.commit()
    
    # Schedule background media downloads
    if new_media_assets:
        background_tasks.add_task(download_assets_batch, new_media_assets)
        logger.info(f"Scheduled {len(new_media_assets)} media assets for background download")
    
    return SearchResponse(
        search_id=search_id,
        platforms=platforms_response,
        results=all_results,
    )
