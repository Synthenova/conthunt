"""Pydantic schemas for TwelveLabs video analysis."""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

class TwelveLabsSearchRequest(BaseModel):
    """Request to search 12Labs index."""
    query: str
    index_id: Optional[str] = None # Optional override, else use env default
    search_options: List[str] = ["visual", "conversation", "text_in_video", "logo"]


class TwelveLabsSearchResponseItem(BaseModel):
    """Single search result item."""
    score: float
    start: float
    end: float
    video_id: str
    confidence: str
    thumbnail_url: Optional[str] = None
    metadata: Optional[dict] = None

class TwelveLabsSearchResponse(BaseModel):
    """Response for search request."""
    data: List[TwelveLabsSearchResponseItem]


class VideoAnalysisRequest(BaseModel):
    """Request to analyze a video (body is empty, content_item_id is path param)."""
    pass


class VideoAnalysisResult(BaseModel):
    """Structured analysis result from 12Labs."""
    hook: Optional[str] = None
    call_to_action: Optional[str] = None
    on_screen_texts: List[str] = []
    key_topics: List[str] = []
    summary: str
    hashtags: List[str] = []
    # Raw data from API in case we need more
    raw: Optional[dict] = None


class VideoAnalysisResponse(BaseModel):
    """Response from video analysis endpoint."""
    id: Optional[UUID] = None
    content_item_id: UUID
    status: str = "processing"  # processing, completed, failed
    analysis: Optional[VideoAnalysisResult] = None
    created_at: Optional[datetime] = None
    cached: bool = False


class TwelvelabsIndexInfo(BaseModel):
    """Info about a 12Labs index."""
    id: UUID
    index_id: str  # 12Labs index ID
    index_name: str
    models: List[dict]
    created_at: datetime


class TwelvelabsAssetInfo(BaseModel):
    """Info about a 12Labs asset."""
    id: UUID
    content_item_id: UUID
    asset_id: str
    indexed_asset_id: Optional[str]
    asset_status: str
    index_status: Optional[str]
    error: Optional[str]
