"""History API endpoints - GET /v1/searches."""
import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import get_current_user
from app.core import logger
from app.db import get_db_connection, set_rls_user, queries
from app.schemas import (
    SearchHistoryItem,
    SearchHistoryResponse,
    SearchDetailResponse,
    PlatformCallInfo,
    SearchResultDetail,
    ContentItemDetail,
    AssetDetail,
)
from app.services.cdn_signer import bulk_sign_gcs_uris, should_sign_asset
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
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    async with get_db_connection() as conn:
        # Get cached user UUID
        
        
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
    logger.debug(f"get_search_detail: request for search_id={search_id}")
    
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    logger.debug(f"get_search_detail: start request processing")
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)

        # Fetch detailed search data in ONE query
        search_data = await queries.get_full_search_detail(conn, search_id)
        
        if not search_data:
            raise HTTPException(status_code=404, detail="Search not found")
    
    # Single-hop requirement: return signed URLs directly.
    uris_to_sign: list[str] = []
    for r in search_data.get("results", []) or []:
        for a in r.get("assets", []) or []:
            if should_sign_asset(a):
                uris_to_sign.append(a["gcs_uri"])

    signed_cache: dict[str, str] = {}
    try:
        signed_cache = await bulk_sign_gcs_uris(uris_to_sign, expiration_seconds=3600, max_concurrency=25)
    except Exception as e:
        # Don't fail the entire response if signing fails; we'll fall back per-asset below.
        logger.warning("Bulk signing failed for search_id=%s: %s", search_id, e)

    response_results = []
    for r in search_data.get("results", []):
        assets = []
        for a in r.get("assets", []):
            source_url = a.get("source_url")
            if should_sign_asset(a):
                try:
                    source_url = signed_cache.get(a["gcs_uri"], source_url)
                except Exception as e:
                    logger.warning(
                        "Failed to sign asset gcs_uri for search_id=%s asset_id=%s: %s",
                        search_id,
                        a.get("id"),
                        e,
                    )
                
            assets.append(AssetDetail(
                id=a["id"],
                asset_type=a["asset_type"],
                source_url=source_url,
            ))
            
        ci = r["content_item"]
        
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
                author_id=ci.get("author_id"),
                author_name=ci.get("author_name"),
                author_url=ci.get("author_url"),
                author_image_url=ci.get("author_image_url"),
                metrics=ci["metrics"] or {},
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
    return response


@router.get("/searches/{search_id}/items/summary")
@router.get("/searches/{search_id}/items/summary/")
async def get_search_items_summary(
    search_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get search items summary for agent - minimal text data + media_asset_id only."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user token")

    async with get_db_connection() as conn:
        
        await set_rls_user(conn, user_uuid)

        search = await queries.get_search_by_id(conn, search_id)
        if not search:
            raise HTTPException(status_code=404, detail="Search not found")

        return await queries.get_search_items_summary(conn, search_id)
