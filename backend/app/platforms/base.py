"""Base platform adapter types and protocols."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Protocol, Any
from enum import Enum

import httpx


class AssetType(str, Enum):
    THUMBNAIL = "thumbnail"
    IMAGE = "image"
    VIDEO = "video"
    AVATAR = "avatar"
    COVER = "cover"


@dataclass
class MediaUrl:
    """Media URL to be downloaded."""
    asset_type: AssetType
    source_url: str
    source_url_list: Optional[list[str]] = None


@dataclass
class NormalizedItem:
    """Normalized content item from any platform."""
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
    metrics: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)
    media_urls: list[MediaUrl] = field(default_factory=list)


@dataclass
class ParsedPlatformResponse:
    """Parsed response from a platform API."""
    items: list[NormalizedItem]
    next_cursor: Optional[dict] = None
    response_meta: dict = field(default_factory=dict)
    raw_response: dict = field(default_factory=dict)


@dataclass
class PlatformCallResult:
    """Result of a platform API call."""
    platform: str
    success: bool
    parsed: Optional[ParsedPlatformResponse] = None
    http_status: Optional[int] = None
    error: Optional[str] = None
    duration_ms: int = 0
    request_params: dict = field(default_factory=dict)


class PlatformAdapter(Protocol):
    """Protocol for platform adapters."""
    
    slug: str
    
    async def fetch(
        self,
        client: httpx.AsyncClient,
        query: str,
        params: dict,
    ) -> dict:
        """
        Fetch data from the platform API.
        
        Args:
            client: Shared httpx AsyncClient
            query: Search query string
            params: Platform-specific parameters
            
        Returns:
            Raw JSON response from the API
        """
        ...
    
    def parse(self, response_json: dict) -> ParsedPlatformResponse:
        """
        Parse raw API response into normalized items.
        
        Args:
            response_json: Raw JSON from the API
            
        Returns:
            Parsed response with normalized items
        """
        ...
