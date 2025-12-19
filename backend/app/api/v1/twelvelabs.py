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
    """
    settings = get_settings()
    client = get_twelvelabs_client()
    
    index_id = request.index_id or settings.TWELVELABS_INDEX_ID
    if not index_id:
        raise HTTPException(status_code=500, detail="TwelveLabs Index ID not configured")

    try:
        # Use the SDK to search
        # Note: The SDK method signature might vary, verifying based on typical SDK usage
        # Assuming client.search.query or similar. 
        # Using the low-level proxy or specific method from our client wrapper if available.
        # If get_twelvelabs_client returns the raw SDK client:
        
        # Adjust based on SDK version 1.1.0
        # Check if we have a wrapper or raw client. 
        # backend/app/services/twelvelabs_client.py would tell us, but for now assuming standard SDK usage
        
        results = client.search.query(
            index_id=index_id,
            query_text=request.query,
            options=request.search_options
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
