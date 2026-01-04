"""Media API schemas."""
from typing import Optional
from pydantic import BaseModel


class SignedUrlResponse(BaseModel):
    """Response for GET /v1/media/{asset_id}/signed-url."""
    url: str
    expires_in: int = 3600


class MediaViewResponse(BaseModel):
    """Response for GET /v1/media/{asset_id}/view - full metadata for ContentDrawer."""
    id: str
    asset_type: str
    url: str  # Signed URL
    title: Optional[str] = None
    platform: Optional[str] = None
    creator: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    published_at: Optional[str] = None
    canonical_url: Optional[str] = None

