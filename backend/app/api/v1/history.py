"""History API endpoints - GET /v1/searches."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

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

router = APIRouter()


@router.get("/searches", response_model=SearchHistoryResponse)
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
        # Get or create user
        user_uuid = await get_or_create_user(conn, firebase_uid)
        
        # Set RLS context
        await set_rls_user(conn, user_uuid)
        
        # Get searches (RLS will filter)
        searches = await queries.get_user_searches(conn, limit=limit)
    
    return SearchHistoryResponse(
        searches=[
            SearchHistoryItem(
                id=s["id"],
                query=s["query"],
                inputs=s["inputs"],
                created_at=s["created_at"],
            )
            for s in searches
        ]
    )


@router.get("/searches/{search_id}", response_model=SearchDetailResponse)
async def get_search_detail(
    search_id: UUID,
    user: dict = Depends(get_current_user),
):
    """
    Get detailed search results.
    
    Includes platform calls, content items with payloads, and media assets.
    """
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    async with get_db_connection() as conn:
        # Get or create user
        user_uuid = await get_or_create_user(conn, firebase_uid)
        
        # Set RLS context
        await set_rls_user(conn, user_uuid)
        
        # Get search (RLS will filter)
        search = await queries.get_search_by_id(conn, search_id)
        if not search:
            raise HTTPException(status_code=404, detail="Search not found")
        
        # Get platform calls
        platform_calls = await queries.get_platform_calls_for_search(conn, search_id)
        
        # Get results with content and assets
        results = await queries.get_search_results_with_content(conn, search_id)
    
    return SearchDetailResponse(
        id=search["id"],
        query=search["query"],
        inputs=search["inputs"],
        mode=search["mode"],
        created_at=search["created_at"],
        platform_calls=[
            PlatformCallInfo(
                id=pc["id"],
                platform=pc["platform"],
                success=pc["success"],
                http_status=pc["http_status"],
                error=pc["error"],
                duration_ms=pc["duration_ms"],
                next_cursor=pc["next_cursor"],
                response_meta=pc["response_meta"] or {},
            )
            for pc in platform_calls
        ],
        results=[
            SearchResultDetail(
                rank=r["rank"],
                content_item=ContentItemDetail(
                    id=r["content_item"]["id"],
                    platform=r["content_item"]["platform"],
                    external_id=r["content_item"]["external_id"],
                    content_type=r["content_item"]["content_type"],
                    canonical_url=r["content_item"]["canonical_url"],
                    title=r["content_item"]["title"],
                    primary_text=r["content_item"]["primary_text"],
                    published_at=r["content_item"]["published_at"],
                    creator_handle=r["content_item"]["creator_handle"],
                    metrics=r["content_item"]["metrics"] or {},
                    payload=r["content_item"]["payload"] or {},
                ),
                assets=[
                    AssetDetail(
                        id=a["id"],
                        asset_type=a["asset_type"],
                        status=a["status"],
                        source_url=a["source_url"],
                        gcs_uri=a["gcs_uri"],
                        sha256=a["sha256"],
                        mime_type=a["mime_type"],
                        bytes=a["bytes"],
                    )
                    for a in r["assets"]
                ],
            )
            for r in results
        ],
    )
