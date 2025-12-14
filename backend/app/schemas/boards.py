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
    # Optional: We could add preview images here later

    model_config = ConfigDict(from_attributes=True)

class BoardItemCreate(BaseModel):
    content_item_id: UUID

class BoardItemResponse(BaseModel):
    board_id: UUID
    content_item: ContentItemResponse
    assets: List[AssetResponse] = []
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)
