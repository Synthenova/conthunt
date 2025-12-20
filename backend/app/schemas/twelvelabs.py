"""Pydantic schemas for TwelveLabs search."""
from pydantic import BaseModel
from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime
from pydantic import validator


class TwelveLabsSearchRequest(BaseModel):
    """Request to search 12Labs index."""
    query: str
    index_id: Optional[str] = None # Optional override, else use env default
    search_options: List[Literal["visual", "audio", "transcription"]] = ["visual", "audio", "transcription"]
    filter: Optional[dict] = None  # Generic filter object
    board_id: Optional[str] = None  # Filter to videos in this board (uses RLS)
    media_asset_id: Optional[str] = None  # Agent uses this - resolved to TwelveLabs ID
    twelvelabs_asset_id: Optional[str] = None  # Direct TwelveLabs ID (for frontend)
    
    @validator("search_options")
    def validate_search_options(cls, v):
        if not v:
            return ["visual", "audio", "transcription"]
        return list(set(v))  # Remove duplicates


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
    media_asset_id: UUID
    asset_id: str
    indexed_asset_id: Optional[str]
    asset_status: str
    index_status: Optional[str]
    error: Optional[str]
