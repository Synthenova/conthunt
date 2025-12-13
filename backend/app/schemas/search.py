"""Search API schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request body for POST /v1/search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    inputs: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Platform-specific parameters keyed by platform slug"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "running",
                "inputs": {
                    "instagram_reels": {"amount": 40},
                    "tiktok_keyword": {"date_posted": "this-week", "sort_by": "relevance"},
                }
            }
        }
    }


class PlatformResult(BaseModel):
    """Result summary for a single platform call."""
    success: bool
    next_cursor: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0
    items_count: int = 0


class AssetResponse(BaseModel):
    """Media asset in response."""
    id: UUID
    asset_type: str
    status: str
    source_url: Optional[str] = None
    gcs_uri: Optional[str] = None


class ContentItemResponse(BaseModel):
    """Content item in response."""
    id: UUID
    platform: str
    external_id: str
    content_type: str
    canonical_url: Optional[str] = None
    title: Optional[str] = None
    primary_text: Optional[str] = None
    published_at: Optional[datetime] = None
    creator_handle: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ResultItem(BaseModel):
    """A single result item with content and assets."""
    rank: int
    content_item: ContentItemResponse
    assets: List[AssetResponse] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Response for POST /v1/search."""
    search_id: UUID
    platforms: Dict[str, PlatformResult]
    results: List[ResultItem]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "search_id": "123e4567-e89b-12d3-a456-426614174000",
                "platforms": {
                    "tiktok_keyword": {
                        "success": True,
                        "next_cursor": {"cursor": 30},
                        "meta": {"credits_remaining": 100},
                        "duration_ms": 1500,
                        "items_count": 20
                    }
                },
                "results": []
            }
        }
    }
