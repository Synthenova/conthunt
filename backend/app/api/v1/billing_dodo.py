"""Billing API endpoints (Dodo Payments)."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.auth import get_current_user, AuthUser
from app.core import get_settings
from app.db import get_db_connection
from app.services.dodo_client import dodo_service
from app.services.credit_tracker import credit_tracker

router = APIRouter(prefix="/billing/dodo", tags=["billing"])


class CreateCheckoutBody(BaseModel):
    """Checkout session request."""
    plan: Literal["creator", "pro_research"]


@router.post("/checkout-session")
async def create_checkout_session(
    body: CreateCheckoutBody, 
    user: AuthUser = Depends(get_current_user)
):
    """Create a Dodo Checkout Session."""
    settings = get_settings()
    
    if body.plan == "creator":
        product_id = settings.DODO_PRODUCT_CREATOR
    elif body.plan == "pro_research":
        product_id = settings.DODO_PRODUCT_PRO
    else:
        raise HTTPException(status_code=400, detail="Invalid plan")

    if not settings.DODO_API_KEY:
        raise HTTPException(status_code=500, detail="Payment configuration missing")

    # Get user's Dodo customer ID if available
    user_id = user["db_user_id"]  # Already a UUID
    customer_id = None
    
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("SELECT dodo_customer_id FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        row = result.fetchone()
        if row and row[0]:
            customer_id = row[0]

    try:
        session = await dodo_service.create_checkout_session(
            product_id=product_id, 
            user_id=user_id,  # Pass internal user_id
            customer_id=customer_id,
        )
        return {
            "checkout_url": session["checkout_url"], 
            "session_id": session["session_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/subscription")
async def get_subscription_status(user: AuthUser = Depends(get_current_user)):
    """
    Get subscription status.
    Reads subscription_id from DB, then fetches live status from Dodo API.
    """
    user_id = user["db_user_id"]  # Already a UUID
    
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            SELECT dodo_subscription_id, role, current_period_start 
            FROM users WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        row = result.fetchone()
        
    if not row or not row[0]:
        return {
            "status": "none",
            "role": row[1] if row else "free",
            "subscription": None
        }
    
    subscription_id = row[0]
    role = row[1]
    period_start = row[2]
    
    # Fetch live status from Dodo
    subscription = await dodo_service.get_subscription(subscription_id)
    
    return {
        "status": subscription["status"] if subscription else "unknown",
        "role": role,
        "current_period_start": period_start.isoformat() if period_start else None,
        "subscription": subscription
    }


@router.get("/usage")
async def get_usage_summary(user: AuthUser = Depends(get_current_user)):
    """Get current usage summary with credits and feature limits."""
    user_id = UUID(user["db_user_id"])
    
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("SELECT role, current_period_start FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = row[0] or "free"
    period_start = row[1]
    
    summary = await credit_tracker.get_usage_summary(
        user_id=user_id,
        role=role,
        current_period_start=period_start
    )
    
    return {"role": role, **summary}
