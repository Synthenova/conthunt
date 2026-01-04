"""History API schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SearchHistoryItem(BaseModel):
    """Search item in history listing."""
    id: UUID
    query: str
    inputs: Dict[str, Any]
    created_at: datetime
    status: str = "completed"  # running, completed, failed


class SearchHistoryResponse(BaseModel):
    """Response for GET /v1/searches."""
    searches: List[SearchHistoryItem]


class PlatformCallInfo(BaseModel):
    """Platform call info for search detail."""
    id: UUID
    platform: str
    success: bool
    http_status: Optional[int] = None
    error: Optional[str] = None
    duration_ms: int
    next_cursor: Optional[Dict[str, Any]] = None
    response_meta: Dict[str, Any] = Field(default_factory=dict)


class AssetDetail(BaseModel):
    """Asset detail in search results."""
    id: UUID
    asset_type: str
    source_url: Optional[str] = None


class ContentItemDetail(BaseModel):
    """Content item detail with all fields."""
    id: UUID
    platform: str
    external_id: str
    content_type: str
    canonical_url: Optional[str] = None
    title: Optional[str] = None
    primary_text: Optional[str] = None
    published_at: Optional[datetime] = None
    creator_handle: Optional[str] = None
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    author_image_url: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class SearchResultDetail(BaseModel):
    """Search result with content and assets for detail view."""
    rank: int
    content_item: ContentItemDetail
    assets: List[AssetDetail] = Field(default_factory=list)


class SearchDetailResponse(BaseModel):
    """Response for GET /v1/searches/{search_id}."""
    id: UUID
    query: str
    inputs: Dict[str, Any]
    mode: str
    status: str = "completed"  # running, completed, failed
    created_at: datetime
    platform_calls: List[PlatformCallInfo]
    results: List[SearchResultDetail]
