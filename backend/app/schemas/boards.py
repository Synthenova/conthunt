from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.search import ContentItemResponse, AssetResponse

class BoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class BoardResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    item_count: Optional[int] = 0
    has_item: bool = False
    preview_urls: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class BoardItemCreate(BaseModel):
    content_item_id: UUID

class BoardItemBatchCreate(BaseModel):
    """Batch add multiple content items to a board."""
    content_item_ids: List[UUID] = Field(..., min_length=1, max_length=100)

class BoardItemResponse(BaseModel):
    board_id: UUID
    content_item: ContentItemResponse
    assets: List[AssetResponse] = []
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)
