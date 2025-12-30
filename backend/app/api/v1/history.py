"""History API endpoints - GET /v1/searches."""
from uuid import UUID
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import get_current_user
from app.core import logger
from app.db import get_db_connection, get_or_create_user, set_rls_user, queries
from app.schemas import (
    SearchHistoryItem,
    SearchHistoryResponse,
    SearchDetailResponse,
    PlatformCallInfo,
    SearchResultDetail,
    ContentItemDetail,
    AssetDetail,
)
from app.services.cdn_signer import generate_signed_url
from app.services.content_builder import extract_author_from_payload
from app.platforms.registry import normalize_platform_slug


def normalize_inputs_for_response(inputs: dict | None) -> dict:
    if not inputs:
        return {}
    normalized: dict = {}
    for slug, params in inputs.items():
        platform = normalize_platform_slug(slug)
        if platform not in normalized:
            normalized[platform] = params
    return normalized

router = APIRouter()


@router.get("/searches", response_model=SearchHistoryResponse)
@router.get("/searches/", response_model=SearchHistoryResponse)
async def list_searches(
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """
    List user's searches, newest first.
    
    Results are automatically filtered by RLS based on user_id.
    """
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    async with get_db_connection() as conn:
        # Get cached user UUID
        from app.services.user_cache import get_cached_user_uuid
        user_uuid = await get_cached_user_uuid(conn, firebase_uid)
        
        # Set RLS context
        await set_rls_user(conn, user_uuid)
        
        # Get searches (RLS will filter)
        searches = await queries.get_user_searches(conn, limit=limit)
    
    return SearchHistoryResponse(
        searches=[
            SearchHistoryItem(
                id=s["id"],
                query=s["query"],
                inputs=normalize_inputs_for_response(s["inputs"]),
                created_at=s["created_at"],
                status=s.get("status", "completed"),
            )
            for s in searches
        ]
    )


@router.get("/searches/{search_id}", response_model=SearchDetailResponse)
@router.get("/searches/{search_id}/", response_model=SearchDetailResponse)
async def get_search_detail(
    search_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    Get detailed search results.
    
    Includes platform calls, content items with payloads, and media assets.
    """
    req_start = time.time()
    logger.info(f"get_search_detail: request for search_id={search_id}")
    
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    logger.info(f"get_search_detail: start request processing")
    
    async with get_db_connection() as conn:
        t0 = time.time()
        # Get cached user UUID (avoids DB hit if cached)
        from app.services.user_cache import get_cached_user_uuid
        user_uuid = await get_cached_user_uuid(conn, firebase_uid)
        logger.info(f"get_search_detail: get_cached_user_uuid took {(time.time()-t0)*1000:.2f}ms")
        
        t0 = time.time()
        # Set RLS context
        await set_rls_user(conn, user_uuid)
        logger.info(f"get_search_detail: set_rls_user took {(time.time()-t0)*1000:.2f}ms")

        # Fetch detailed search data in ONE query
        search_data = await queries.get_full_search_detail(conn, search_id)
        logger.info(f"get_search_detail: get_full_search_detail took {(time.time()-t0)*1000:.2f}ms")
        
        if not search_data:
            raise HTTPException(status_code=404, detail="Search not found")
    
    # Sign URLs for assets (this is CPU bound, fast)
    response_results = []
    for r in search_data.get("results", []):
        assets = []
        for a in r.get("assets", []):
            source_url = a.get("source_url")
            if a.get("status") in ("stored", "downloaded") and a.get("gcs_uri"):
                source_url = generate_signed_url(a["gcs_uri"])
                
            assets.append(AssetDetail(
                id=a["id"],
                asset_type=a["asset_type"],
                status=a["status"],
                source_url=source_url,
                gcs_uri=a["gcs_uri"],
                sha256=a["sha256"],
                mime_type=a["mime_type"],
                bytes=a["bytes"],
            ))
            
        ci = r["content_item"]
        payload = ci.get("payload") or {}
        platform = ci["platform"]
        
        # Extract author info from payload using shared utility
        author_info = extract_author_from_payload(platform, payload, ci.get("creator_handle"))
        
        response_results.append(SearchResultDetail(
            rank=r["rank"],
            content_item=ContentItemDetail(
                id=ci["id"],
                platform=ci["platform"],
                external_id=ci["external_id"],
                content_type=ci["content_type"],
                canonical_url=ci["canonical_url"],
                title=ci["title"],
                primary_text=ci["primary_text"],
                published_at=ci["published_at"],
                creator_handle=ci["creator_handle"],
                author_id=author_info["author_id"],
                author_name=author_info["author_name"],
                author_url=author_info["author_url"],
                author_image_url=author_info["author_image_url"],
                metrics=ci["metrics"] or {},
                payload=ci["payload"] or {},
            ),
            assets=assets
        ))

    response = SearchDetailResponse(
        id=search_data["id"],
        query=search_data["query"],
        inputs=normalize_inputs_for_response(search_data["inputs"]),
        mode=search_data["mode"],
        status=search_data.get("status", "completed"),
        created_at=search_data["created_at"],
        platform_calls=[
            PlatformCallInfo(
                id=pc["id"],
                platform=normalize_platform_slug(pc["platform"]),
                success=pc["success"],
                http_status=pc["http_status"],
                error=pc["error"],
                duration_ms=pc["duration_ms"],
                next_cursor=pc["next_cursor"],
                response_meta=pc["response_meta"] or {},
            )
            for pc in search_data.get("platform_calls", [])
        ],
        results=response_results
    )
    
    duration = (time.time() - req_start) * 1000
    logger.info(f"get_search_detail: finished search_id={search_id} duration={duration:.2f}ms")
    return response


@router.get("/searches/{search_id}/items/summary")
@router.get("/searches/{search_id}/items/summary/")
async def get_search_items_summary(
    search_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get search items summary for agent - minimal text data + media_asset_id only."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user token")

    async with get_db_connection() as conn:
        from app.services.user_cache import get_cached_user_uuid
        user_uuid = await get_cached_user_uuid(conn, firebase_uid)
        await set_rls_user(conn, user_uuid)

        search = await queries.get_search_by_id(conn, search_id)
        if not search:
            raise HTTPException(status_code=404, detail="Search not found")

        return await queries.get_search_items_summary(conn, search_id)
