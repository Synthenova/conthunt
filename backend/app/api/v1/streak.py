"""Streak tracking endpoints."""
from fastapi import APIRouter, Depends, Query

from app.auth import get_current_user, AuthUser
from app.db.session import get_db_connection
from app.db.queries import streaks as streak_queries

router = APIRouter(prefix="/streak", tags=["streak"])


@router.get("")
async def get_streak(
    user: AuthUser = Depends(get_current_user),
    timezone: str = Query(default="UTC", description="User's timezone for day calculation")
):
    """
    Get user's current streak data and milestones.
    
    Returns:
        - current_streak: Number of consecutive days
        - longest_streak: All-time longest streak
        - next_milestone: Next milestone to achieve
        - milestones: All available milestones with completion status
        - today_complete: Whether today's requirement is met
    """
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        # Ensure record exists and check for streak reset
        streak = await streak_queries.ensure_streak_record(conn, user_id, timezone)
        user_today = streak_queries.get_user_today(timezone)
        streak = await streak_queries.check_streak_reset(conn, user_id, user_today)
        
        # Get milestones
        milestones = await streak_queries.get_milestones(conn)
        next_milestone = await streak_queries.get_next_milestone(streak["current_streak"], milestones)
        
        # Check if today's requirement is complete
        today_complete = False
        app_opened_today = False
        search_done_today = False
        
        if streak["last_app_open_at"]:
            try:
                from zoneinfo import ZoneInfo
                app_open_date = streak["last_app_open_at"].astimezone(ZoneInfo(timezone)).date()
                app_opened_today = app_open_date == user_today
            except Exception:
                pass
        
        if streak["last_search_at"]:
            try:
                from zoneinfo import ZoneInfo
                search_date = streak["last_search_at"].astimezone(ZoneInfo(timezone)).date()
                search_done_today = search_date == user_today
            except Exception:
                pass
        
        today_complete = app_opened_today and search_done_today
        
        # Enrich milestones with completion status
        enriched_milestones = []
        for m in milestones:
            enriched_milestones.append({
                **m,
                "completed": streak["current_streak"] >= m["days_required"],
            })
        
        return {
            "current_streak": streak["current_streak"],
            "longest_streak": streak["longest_streak"],
            "last_activity_date": streak["last_activity_date"].isoformat() if streak["last_activity_date"] else None,
            "next_milestone": next_milestone,
            "milestones": enriched_milestones,
            "today_complete": today_complete,
            "today_status": {
                "app_opened": app_opened_today,
                "search_done": search_done_today,
            }
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
        streak = await streak_queries.record_app_open(conn, user_id, timezone)
        
        return {
            "success": True,
            "current_streak": streak["current_streak"],
        }
