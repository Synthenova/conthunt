"""Media API schemas."""
from pydantic import BaseModel


class SignedUrlResponse(BaseModel):
    """Response for GET /v1/media/{asset_id}/signed-url."""
    url: str
    expires_in: int = 3600
