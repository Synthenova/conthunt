"""Streak tracking endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import get_current_user, AuthUser
from app.db import set_rls_user
from app.db.session import get_db_connection
from app.db.queries import streaks as streak_queries

router = APIRouter(prefix="/streak", tags=["streak"])

class ClaimRewardRequest(BaseModel):
    streak_type: str = Field(default="open", alias="type")
    days_required: int


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
        claimed_days = await streak_queries.get_claimed_days(conn, user_id, role, streak_type)
        next_milestone = await streak_queries.get_next_milestone(streak["current_streak"], milestones)
        
        # Check if today's requirement is complete
        today_complete = await streak_queries.get_today_status(
            conn,
            user_id,
            streak_type,
            user_today,
        )
        
        # Enrich milestones with completion status + claim state
        enriched_milestones = []
        for m in milestones:
            enriched_milestones.append({
                **m,
                "completed": streak["current_streak"] >= m["days_required"],
                "claimed": m["days_required"] in claimed_days,
                "claimable": (
                    streak["current_streak"] >= m["days_required"]
                    and m["days_required"] not in claimed_days
                ),
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


@router.post("/claim")
async def claim_reward(
    request: ClaimRewardRequest,
    user: AuthUser = Depends(get_current_user),
):
    """Manually claim a streak reward for a milestone."""
    user_id = user["db_user_id"]
    role = user.get("role", "free")
    streak_type = request.streak_type
    days_required = request.days_required

    async with get_db_connection() as conn:
        await set_rls_user(conn, user_id)
        try:
            streak = await streak_queries.ensure_user_streak(conn, user_id, streak_type)
            milestone = await streak_queries.get_milestone_for_claim(
                conn, role, streak_type, days_required
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone not found")

        reward_feature = milestone.get("reward_feature")
        reward_credits = milestone.get("reward_credits", 0)
        reward_feature_amount = milestone.get("reward_feature_amount", 0)
        if reward_credits <= 0 and reward_feature_amount <= 0:
            raise HTTPException(status_code=400, detail="Milestone reward is not configured")
        if reward_feature_amount > 0 and not reward_feature:
            raise HTTPException(status_code=400, detail="Milestone reward feature is not configured")

        if streak["current_streak"] < days_required:
            raise HTTPException(status_code=400, detail="Milestone not yet reached")

        grant = await streak_queries.grant_reward(
            conn, user_id, role, streak_type, milestone
        )
        if not grant:
            return {
                "claimed": False,
                "reason": "already_claimed",
                "reward": {
                    "feature": reward_feature,
                    "credits": reward_credits,
                    "feature_amount": reward_feature_amount,
                    "days_required": days_required,
                },
            }

        return {
            "claimed": True,
            "reward": {
                "feature": reward_feature,
                "credits": reward_credits,
                "feature_amount": reward_feature_amount,
                "days_required": days_required,
            },
            "balances": grant,
        }
