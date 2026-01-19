"""Onboarding tutorial endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, AuthUser
from app.db import set_rls_user
from app.db.session import get_db_connection
from app.db.queries import onboarding as onboarding_queries
from app.core.onboarding_flows import get_flow, get_all_flows, ONBOARDING_FLOWS
from app.schemas.onboarding import (
    FlowSummary,
    FlowDetail,
    FlowStepSchema,
    ProgressStatus,
    FlowWithProgress,
    StartFlowRequest,
    CompleteStepRequest,
    SkipFlowRequest,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/flows", response_model=List[FlowSummary])
async def list_flows():
    """
    List all available tutorial flows.
    Used for profile dropdown menu.
    """
    flows = get_all_flows()
    return [
        FlowSummary(
            id=flow.id,
            name=flow.name,
            page=flow.page,
            total_steps=flow.total_steps
        )
        for flow in flows
    ]


@router.get("/status", response_model=List[ProgressStatus])
async def get_all_status(
    user: AuthUser = Depends(get_current_user)
):
    """
    Get user's progress status for all flows.
    Returns status for each flow (not_started if never accessed).
    """
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        progress_list = await onboarding_queries.get_all_user_progress(conn, user_id)
    
    # Create a map of flow_id -> progress
    progress_map = {p["flow_id"]: p for p in progress_list}
    
    # Return status for ALL flows (including not started)
    result = []
    for flow_id, flow_data in ONBOARDING_FLOWS.items():
        if flow_id in progress_map:
            prog = progress_map[flow_id]
            result.append(ProgressStatus(
                flow_id=flow_id,
                status=prog["status"],
                current_step=prog["current_step"],
                total_steps=len(flow_data["steps"]),
                restart_count=prog["restart_count"]
            ))
        else:
            result.append(ProgressStatus(
                flow_id=flow_id,
                status="not_started",
                current_step=0,
                total_steps=len(flow_data["steps"]),
                restart_count=0
            ))
    
    return result


@router.get("/status/{flow_id}", response_model=FlowWithProgress)
async def get_flow_status(
    flow_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """
    Get status for a specific flow with full flow details.
    Used when page loads to check if tutorial should auto-start.
    """
    flow = get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")
    
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        progress = await onboarding_queries.get_user_progress(conn, user_id, flow_id)
    
    if progress:
        progress_status = ProgressStatus(
            flow_id=flow_id,
            status=progress["status"],
            current_step=progress["current_step"],
            total_steps=flow.total_steps,
            restart_count=progress["restart_count"]
        )
    else:
        progress_status = ProgressStatus(
            flow_id=flow_id,
            status="not_started",
            current_step=0,
            total_steps=flow.total_steps,
            restart_count=0
        )
    
    return FlowWithProgress(
        flow=FlowDetail(
            id=flow.id,
            name=flow.name,
            page=flow.page,
            total_steps=flow.total_steps,
            steps=[FlowStepSchema(**step.model_dump()) for step in flow.steps]
        ),
        progress=progress_status
    )


@router.post("/start", response_model=ProgressStatus)
async def start_flow_endpoint(
    request: StartFlowRequest,
    user: AuthUser = Depends(get_current_user)
):
    """
    Start or restart a tutorial flow.
    
    - If flow not started: starts at step 1
    - If replay=true: resets to step 1, increments restart_count
    - If in-progress without replay: returns current state
    """
    flow = get_flow(request.flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{request.flow_id}' not found")
    
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        result = await onboarding_queries.start_flow(
            conn, user_id, request.flow_id, request.replay
        )
    
    return ProgressStatus(
        flow_id=result["flow_id"],
        status=result["status"],
        current_step=result["current_step"],
        total_steps=flow.total_steps,
        restart_count=result["restart_count"]
    )


@router.post("/step", response_model=ProgressStatus)
async def complete_step_endpoint(
    request: CompleteStepRequest,
    user: AuthUser = Depends(get_current_user)
):
    """
    Complete the current step and advance to next.
    
    If this is the last step, marks flow as completed.
    """
    flow = get_flow(request.flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{request.flow_id}' not found")
    
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        result = await onboarding_queries.complete_step(
            conn, user_id, request.flow_id, flow.total_steps
        )
    
    return ProgressStatus(
        flow_id=result["flow_id"],
        status=result["status"],
        current_step=result["current_step"],
        total_steps=flow.total_steps,
        restart_count=result["restart_count"]
    )


@router.post("/skip", response_model=ProgressStatus)
async def skip_flow_endpoint(
    request: SkipFlowRequest,
    user: AuthUser = Depends(get_current_user)
):
    """
    Skip a tutorial flow entirely.
    
    Sets status to 'skipped'. Can still be replayed later.
    """
    flow = get_flow(request.flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{request.flow_id}' not found")
    
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        result = await onboarding_queries.skip_flow(conn, user_id, request.flow_id)
    
    return ProgressStatus(
        flow_id=result["flow_id"],
        status=result["status"],
        current_step=result["current_step"],
        total_steps=flow.total_steps,
        restart_count=result["restart_count"]
    )
