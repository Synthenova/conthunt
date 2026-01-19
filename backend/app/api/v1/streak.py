"""Streak tracking endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user, AuthUser
from app.db import set_rls_user
from app.db.session import get_db_connection
from app.db.queries import streaks as streak_queries

router = APIRouter(prefix="/streak", tags=["streak"])


@router.get("")
async def get_streak(
    user: AuthUser = Depends(get_current_user),
    streak_type: str = Query(default="open", alias="type", description="Streak type slug")
):
    """
    Get user's current streak data and milestones.
    
    Returns:
        - type: Streak type slug
        - current_streak: Number of consecutive days
        - longest_streak: All-time longest streak
        - last_activity_date: Last date counted for streak
        - last_action_at: Timestamp of most recent action
        - today_complete: Whether today's activity is complete
        - milestones: Milestones for role + type
        - next_milestone: Next milestone to achieve
    """
    user_id = user["db_user_id"]
    role = user.get("role", "free")
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        try:
            timezone = await streak_queries.get_user_timezone(conn, user_id)
            user_today = streak_queries.get_user_today(timezone)
            streak = await streak_queries.ensure_user_streak(conn, user_id, streak_type)
            streak = await streak_queries.reset_streak_if_missed(conn, user_id, streak_type, user_today)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        
        # Get milestones
        milestones = await streak_queries.get_milestones(conn, role, streak_type)
        next_milestone = await streak_queries.get_next_milestone(streak["current_streak"], milestones)
        
        # Check if today's requirement is complete
        today_complete = await streak_queries.get_today_status(
            conn,
            user_id,
            streak_type,
            user_today,
        )
        
        # Enrich milestones with completion status
        enriched_milestones = []
        for m in milestones:
            enriched_milestones.append({
                **m,
                "completed": streak["current_streak"] >= m["days_required"],
            })
        
        return {
            "type": streak_type,
            "timezone": timezone,
            "current_streak": streak["current_streak"],
            "longest_streak": streak["longest_streak"],
            "last_activity_date": streak["last_activity_date"].isoformat() if streak["last_activity_date"] else None,
            "last_action_at": streak["last_action_at"].isoformat() if streak["last_action_at"] else None,
            "today_complete": today_complete,
            "milestones": enriched_milestones,
            "next_milestone": next_milestone,
        }


@router.post("/open")
async def record_app_open(
    user: AuthUser = Depends(get_current_user),
    timezone: str = Query(default="UTC", description="User's timezone")
):
    """
    Record app open event.
    Called when user opens the app/loads the page.
    """
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        await streak_queries.set_user_timezone(conn, user_id, timezone)
        streak = await streak_queries.record_activity(conn, user_id, "open", timezone=timezone)
        
        return {
            "success": True,
            "current_streak": streak["current_streak"],
        }
