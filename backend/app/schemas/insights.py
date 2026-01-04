from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CommonAngle(BaseModel):
    label: str = Field(..., description="Common creative angle")
    percentage: float = Field(..., description="Share of videos using this angle")


class CreativeBrief(BaseModel):
    target_audience: str = Field(..., description="Primary audience segment")
    key_message: str = Field(..., description="Main message to communicate")
    recommended_format: str = Field(..., description="Recommended content format")


class BoardInsightsResult(BaseModel):
    top_hooks: List[str] = Field(default_factory=list, description="High-performing hook ideas")
    common_angles: List[CommonAngle] = Field(default_factory=list, description="Recurring angles and their shares")
    creative_brief: CreativeBrief
    script_ideas: List[str] = Field(default_factory=list, description="Script ideas to try")
    objections: List[str] = Field(default_factory=list, description="Common objections from the audience")
    ctas: List[str] = Field(default_factory=list, description="Effective calls to action")


class BoardInsightsProgress(BaseModel):
    total_videos: int = Field(0, description="Total videos in board to analyze")
    analyzed_videos: int = Field(0, description="Number of videos with completed analysis")
    failed_videos: int = Field(0, description="Number of videos where analysis failed")


class BoardInsightsResponse(BaseModel):
    id: Optional[UUID] = None
    board_id: UUID
    status: str = "processing"  # empty, processing, completed, failed
    insights: Optional[BoardInsightsResult] = None
    progress: Optional[BoardInsightsProgress] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_completed_at: Optional[datetime] = None
