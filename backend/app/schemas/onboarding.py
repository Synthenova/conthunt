"""Onboarding schemas for API request/response models."""
from typing import List, Optional
from pydantic import BaseModel


class FlowStepSchema(BaseModel):
    """Single step in a tutorial flow. Targets are managed in frontend."""
    id: str
    title: str
    content: str
    cta: Optional[dict] = None


class FlowSummary(BaseModel):
    """Summary of a flow for listing."""
    id: str
    name: str
    page: str
    total_steps: int


class FlowDetail(BaseModel):
    """Full flow with all steps."""
    id: str
    name: str
    page: str
    total_steps: int
    steps: List[FlowStepSchema]


class ProgressStatus(BaseModel):
    """User's progress on a single flow."""
    flow_id: str
    status: str  # not_started, in_progress, completed, skipped
    current_step: int
    total_steps: int
    restart_count: int = 0


class FlowWithProgress(BaseModel):
    """Flow details combined with user progress."""
    flow: FlowDetail
    progress: ProgressStatus


class StartFlowRequest(BaseModel):
    """Request to start or restart a flow."""
    flow_id: str
    replay: bool = False


class CompleteStepRequest(BaseModel):
    """Request to complete current step."""
    flow_id: str


class SkipFlowRequest(BaseModel):
    """Request to skip a flow."""
    flow_id: str
