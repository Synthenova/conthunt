"""Database queries for onboarding progress tracking."""
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def get_user_progress(
    conn: AsyncConnection,
    user_id: UUID,
    flow_id: str
) -> Optional[Dict[str, Any]]:
    """Get user's progress for a specific flow."""
    result = await conn.execute(
        text("""
            SELECT 
                flow_id,
                current_step,
                status,
                started_at,
                completed_at,
                restart_count
            FROM user_onboarding_progress
            WHERE user_id = :user_id AND flow_id = :flow_id
        """),
        {"user_id": user_id, "flow_id": flow_id}
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "flow_id": row.flow_id,
        "current_step": row.current_step,
        "status": row.status,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "restart_count": row.restart_count,
    }


async def get_all_user_progress(
    conn: AsyncConnection,
    user_id: UUID
) -> List[Dict[str, Any]]:
    """Get user's progress for all flows."""
    result = await conn.execute(
        text("""
            SELECT 
                flow_id,
                current_step,
                status,
                started_at,
                completed_at,
                restart_count
            FROM user_onboarding_progress
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    return [
        {
            "flow_id": row.flow_id,
            "current_step": row.current_step,
            "status": row.status,
            "started_at": row.started_at,
            "completed_at": row.completed_at,
            "restart_count": row.restart_count,
        }
        for row in result.fetchall()
    ]


async def start_flow(
    conn: AsyncConnection,
    user_id: UUID,
    flow_id: str,
    replay: bool = False
) -> Dict[str, Any]:
    """
    Start or restart a flow.
    
    If replay=True and flow exists, reset progress and increment restart_count.
    If flow doesn't exist, create new progress record.
    """
    if replay:
        # Try to update existing record (replay)
        result = await conn.execute(
            text("""
                UPDATE user_onboarding_progress
                SET 
                    current_step = 1,
                    status = 'in_progress',
                    started_at = NOW(),
                    completed_at = NULL,
                    updated_at = NOW(),
                    restart_count = restart_count + 1
                WHERE user_id = :user_id AND flow_id = :flow_id
                RETURNING flow_id, current_step, status, restart_count
            """),
            {"user_id": user_id, "flow_id": flow_id}
        )
        row = result.fetchone()
        if row:
            await conn.commit()
            return {
                "flow_id": row.flow_id,
                "current_step": row.current_step,
                "status": row.status,
                "restart_count": row.restart_count,
            }
    
    # Insert new or start existing (non-replay)
    result = await conn.execute(
        text("""
            INSERT INTO user_onboarding_progress (user_id, flow_id, current_step, status, started_at)
            VALUES (:user_id, :flow_id, 1, 'in_progress', NOW())
            ON CONFLICT (user_id, flow_id) 
            DO UPDATE SET 
                current_step = CASE 
                    WHEN user_onboarding_progress.status = 'not_started' THEN 1
                    ELSE user_onboarding_progress.current_step
                END,
                status = CASE 
                    WHEN user_onboarding_progress.status = 'not_started' THEN 'in_progress'
                    ELSE user_onboarding_progress.status
                END,
                started_at = CASE 
                    WHEN user_onboarding_progress.started_at IS NULL THEN NOW()
                    ELSE user_onboarding_progress.started_at
                END,
                updated_at = NOW()
            RETURNING flow_id, current_step, status, restart_count
        """),
        {"user_id": user_id, "flow_id": flow_id}
    )
    row = result.fetchone()
    await conn.commit()
    return {
        "flow_id": row.flow_id,
        "current_step": row.current_step,
        "status": row.status,
        "restart_count": row.restart_count,
    }


async def complete_step(
    conn: AsyncConnection,
    user_id: UUID,
    flow_id: str,
    total_steps: int
) -> Dict[str, Any]:
    """
    Mark current step as complete and advance to next.
    
    If this was the last step, mark flow as completed.
    """
    # Get current progress
    current = await get_user_progress(conn, user_id, flow_id)
    if not current:
        # Flow not started - start it first
        return await start_flow(conn, user_id, flow_id)
    
    new_step = current["current_step"] + 1
    
    if new_step > total_steps:
        # All steps complete
        result = await conn.execute(
            text("""
                UPDATE user_onboarding_progress
                SET 
                    current_step = :new_step,
                    status = 'completed',
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE user_id = :user_id AND flow_id = :flow_id
                RETURNING flow_id, current_step, status, restart_count
            """),
            {"user_id": user_id, "flow_id": flow_id, "new_step": new_step}
        )
    else:
        # Advance to next step
        result = await conn.execute(
            text("""
                UPDATE user_onboarding_progress
                SET 
                    current_step = :new_step,
                    updated_at = NOW()
                WHERE user_id = :user_id AND flow_id = :flow_id
                RETURNING flow_id, current_step, status, restart_count
            """),
            {"user_id": user_id, "flow_id": flow_id, "new_step": new_step}
        )
    
    row = result.fetchone()
    await conn.commit()
    return {
        "flow_id": row.flow_id,
        "current_step": row.current_step,
        "status": row.status,
        "restart_count": row.restart_count,
    }


async def skip_flow(
    conn: AsyncConnection,
    user_id: UUID,
    flow_id: str
) -> Dict[str, Any]:
    """Mark a flow as skipped."""
    result = await conn.execute(
        text("""
            INSERT INTO user_onboarding_progress (user_id, flow_id, status, completed_at)
            VALUES (:user_id, :flow_id, 'skipped', NOW())
            ON CONFLICT (user_id, flow_id)
            DO UPDATE SET 
                status = 'skipped',
                completed_at = NOW(),
                updated_at = NOW()
            RETURNING flow_id, current_step, status, restart_count
        """),
        {"user_id": user_id, "flow_id": flow_id}
    )
    row = result.fetchone()
    await conn.commit()
    return {
        "flow_id": row.flow_id,
        "current_step": row.current_step,
        "status": row.status,
        "restart_count": row.restart_count,
    }
