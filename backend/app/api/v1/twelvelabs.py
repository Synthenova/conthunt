"""TwelveLabs video analysis API endpoints."""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from app.auth.firebase import get_current_user
from app.core.settings import get_settings
from app.schemas.twelvelabs import (
    TwelveLabsSearchRequest,
    TwelveLabsSearchResponse,
    TwelveLabsSearchResponseItem
)
from app.services.twelvelabs_client import get_twelvelabs_client

from app.db.session import get_db_connection
from app.db.queries.twelvelabs import get_twelvelabs_asset_by_content_item, get_user_twelvelabs_assets
from app.db import get_or_create_user, set_rls_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["video-analysis"])

@router.post(
    "/search",
    response_model=TwelveLabsSearchResponse,
    summary="Search TwelveLabs Index",
)
async def search_twelvelabs(
    request: TwelveLabsSearchRequest,
    _user: dict = Depends(get_current_user),
):
    """
    Search the TwelveLabs index for video clips matching the query.
    Supports filtering by content_item_id to search within a specific video.
    """
    settings = get_settings()
    client = get_twelvelabs_client()
    
    index_id = request.index_id or settings.TWELVELABS_INDEX_ID
    if not index_id:
        raise HTTPException(status_code=500, detail="TwelveLabs Index ID not configured")

    search_filter = request.filter or {}

    # Filter by specific TwelveLabs asset ID if provided
    # This comes directly from the frontend/client so no DB lookup needed
    if request.twelvelabs_asset_id:
        # Marengo 3.0 uses 'id' in filter for video IDs
        search_filter["id"] = [request.twelvelabs_asset_id]
    else:
        # Default: Search all user's indexed assets across all boards
        firebase_uid = _user.get("uid")
        if not firebase_uid:
             raise HTTPException(status_code=401, detail="Invalid user")
        
        async with get_db_connection() as conn:
            user_uuid, _ = await get_or_create_user(conn, firebase_uid)
            await set_rls_user(conn, user_uuid)
            
            assets = await get_user_twelvelabs_assets(conn)
            
            if not assets:
                # Return empty response if no videos indexed
                return TwelveLabsSearchResponse(data=[])
            
            search_filter["id"] = assets
        
    try:
        results = client.search.query(
            index_id=index_id,
            query_text=request.query,
            options=request.search_options,
            filter=search_filter if search_filter else None
        )
        
        # Map SDK results to schema
        # The SDK returns an iterator/list of SearchItem
        response_items = []
        for item in results:
             response_items.append(TwelveLabsSearchResponseItem(
                 score=getattr(item, "score", 0.0),
                 start=item.start,
                 end=item.end,
                 video_id=item.video_id,
                 confidence=getattr(item, "confidence", "medium"),
                 thumbnail_url=item.thumbnail_url,
                 metadata=item.metadata if hasattr(item, "metadata") else None
             ))
             
        return TwelveLabsSearchResponse(data=response_items)

    except Exception as e:
        logger.error(f"TwelveLabs search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
