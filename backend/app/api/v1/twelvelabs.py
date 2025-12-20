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
from app.db.queries.twelvelabs import get_user_twelvelabs_assets, get_twelvelabs_id_for_media_asset, get_board_twelvelabs_assets
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
    Supports filtering by board_id, media_asset_id, or direct twelvelabs_asset_id.
    """
    settings = get_settings()
    client = get_twelvelabs_client()
    
    index_id = request.index_id or settings.TWELVELABS_INDEX_ID
    if not index_id:
        raise HTTPException(status_code=500, detail="TwelveLabs Index ID not configured")

    search_filter = request.filter or {}
    
    firebase_uid = _user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
        await set_rls_user(conn, user_uuid)
        
        # Priority: media_asset_id > twelvelabs_asset_id > board_id > all user assets
        if request.media_asset_id:
            # Agent sends media_asset_id - resolve to TwelveLabs ID
            tl_id = await get_twelvelabs_id_for_media_asset(conn, UUID(request.media_asset_id))
            if not tl_id:
                raise HTTPException(status_code=404, detail="Video not indexed in TwelveLabs")
            search_filter["id"] = [tl_id]
            
        elif request.twelvelabs_asset_id:
            # Direct TwelveLabs ID (from frontend)
            search_filter["id"] = [request.twelvelabs_asset_id]
        
        elif request.board_id:
            # Filter to a specific board
            assets = await get_board_twelvelabs_assets(conn, UUID(request.board_id))
            if not assets:
                return TwelveLabsSearchResponse(data=[])
            search_filter["id"] = assets
            
        else:
            # Default: Search all user's indexed assets across all boards
            assets = await get_user_twelvelabs_assets(conn)
            
            if not assets:
                # Return empty response if no videos indexed
                return TwelveLabsSearchResponse(data=[])
            
            search_filter["id"] = assets
        
    try:
        # Call the async search method on our wrapper
        results = await client.search(
            index_id=index_id,
            query_text=request.query,
            search_options=request.search_options,
            filter=search_filter if search_filter else None,
        )
        
        # Map SDK results to schema (Marengo 3.0 uses `rank`)
        response_items = []
        for item in results:
            rank = getattr(item, "rank", 1)
            
            # Convert rank to confidence: 1-3 = high, 4-10 = medium, 11+ = low
            if rank <= 3:
                confidence = "high"
            elif rank <= 10:
                confidence = "medium"
            else:
                confidence = "low"
            
            response_items.append(TwelveLabsSearchResponseItem(
                score=1.0 / rank if rank > 0 else 1.0,
                start=item.start,
                end=item.end,
                video_id=item.video_id,
                confidence=confidence,
                thumbnail_url=item.thumbnail_url,
                metadata=item.user_metadata if hasattr(item, "user_metadata") else None,
            ))
             
        return TwelveLabsSearchResponse(data=response_items)

    except Exception as e:
        logger.error(f"TwelveLabs search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
