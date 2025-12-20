from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class VideoAnalysisResult(BaseModel):
    """Structured analysis result."""
    hook: Optional[str] = Field(None, description="The attention-grabbing opening hook")
    call_to_action: Optional[str] = Field(None, description="Call to action for viewer engagement")
    on_screen_texts: List[str] = Field(default_factory=list, description="Text overlays captured")
    key_topics: List[str] = Field(default_factory=list, description="Main topics or themes")
    summary: str = Field(..., description="Brief summary of the content")
    hashtags: List[str] = Field(default_factory=list, description="Suggested hashtags")
    
class VideoAnalysisResponse(BaseModel):
    """Response from video analysis endpoint."""
    id: Optional[UUID] = None
    media_asset_id: UUID
    status: str = "processing"  # processing, completed, failed
    analysis: Optional[VideoAnalysisResult] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    cached: bool = False

