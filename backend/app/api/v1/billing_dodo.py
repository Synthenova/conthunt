"""Billing API endpoints (Dodo Payments)."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.auth import get_current_user, AuthUser
from app.core import get_settings
from app.db import get_db_connection
from app.db.queries import billing as billing_queries
from app.services.dodo_client import dodo_service
from app.services.credit_tracker import credit_tracker

router = APIRouter(prefix="/billing/dodo", tags=["billing"])


class CreateCheckoutBody(BaseModel):
    """Checkout session request."""
    plan: Literal["creator", "pro_research"]
    interval: Literal["monthly", "yearly"] = "monthly"


class ScheduleDowngradeBody(BaseModel):
    """Schedule downgrade request."""
    target_plan: Literal["creator", "free"]


@router.get("/products")
async def list_available_products():
    """
    List all available subscription products.
    Dynamically fetched from Dodo API based on product metadata.
    """
    try:
        products = await dodo_service.get_products_for_checkout()
        
        # Format for frontend
        return {
            "products": [
                {
                    "product_id": p["product_id"],
                    "name": p["name"],
                    "plan": p["app_role"],
                    "interval": p["billing_interval"],
                    "price": p["price"],
                    "currency": p["currency"],
                }
                for p in products
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch products")


@router.post("/checkout-session")
async def create_checkout_session(
    body: CreateCheckoutBody, 
    user: AuthUser = Depends(get_current_user)
):
    """Create a Dodo Checkout Session using dynamic product lookup."""
    settings = get_settings()

    if not settings.DODO_API_KEY:
        raise HTTPException(status_code=500, detail="Payment configuration missing")

    # Dynamic product lookup by role and interval
    product = await dodo_service.get_product_by_role_and_interval(
        app_role=body.plan,
        billing_interval=body.interval,
    )
    
    if not product:
        raise HTTPException(
            status_code=400, 
            detail=f"No product found for plan={body.plan}, interval={body.interval}"
        )
    
    product_id = product["product_id"]

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
            user_id=user_id,
            customer_id=customer_id,
        )
        return {
            "checkout_url": session["checkout_url"], 
            "session_id": session["session_id"],
            "product_id": product_id,
            "plan": body.plan,
            "interval": body.interval,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/subscription")
async def get_subscription_status(user: AuthUser = Depends(get_current_user)):
    """
    Get subscription status.
    Returns normalized subscription state from DB plus live Dodo status.
    Includes pending downgrade info if any.
    """
    user_id = user["db_user_id"]  # Already a UUID
    
    async with get_db_connection() as conn:
        # Get user info
        result = await conn.execute(
            text("""
            SELECT dodo_subscription_id, role, current_period_start 
            FROM users WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        user_row = result.fetchone()
        
        if not user_row:
            return {
                "status": "none",
                "role": "free",
                "subscription": None,
                "pending_downgrade": None,
            }
        
        subscription_id = user_row[0]
        role = user_row[1] or "free"
        period_start = user_row[2]
        
        # Get normalized subscription from our DB
        sub_data = await billing_queries.get_user_subscription(conn, user_id)
        
        # Get pending downgrade
        pending = await billing_queries.get_pending_plan_change(conn, user_id)
    
    # Build response
    response = {
        "role": role,
        "current_period_start": period_start.isoformat() if period_start else None,
        "pending_downgrade": None,
    }
    
    if sub_data:
        response["status"] = sub_data.get("status", "unknown")
        response["cancel_at_next_billing_date"] = sub_data.get("cancel_at_next_billing_date", False)
        response["current_period_end"] = sub_data["current_period_end"].isoformat() if sub_data.get("current_period_end") else None
        
        # Optionally fetch live status from Dodo
        if subscription_id:
            live_sub = await dodo_service.get_subscription(subscription_id)
            if live_sub:
                response["live_status"] = live_sub.get("status")
    else:
        response["status"] = "none" if not subscription_id else "unknown"
        response["cancel_at_next_billing_date"] = False
        response["current_period_end"] = None
    
    if pending:
        response["pending_downgrade"] = {
            "target_plan": pending["target_role"],
            "effective_at": pending["effective_at"].isoformat() if pending["effective_at"] else None,
            "created_at": pending["created_at"].isoformat() if pending["created_at"] else None,
        }
    
    return response


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


# ============================================================================
# SCHEDULED DOWNGRADE ENDPOINTS
# ============================================================================

@router.post("/schedule-downgrade")
async def schedule_downgrade(
    body: ScheduleDowngradeBody,
    user: AuthUser = Depends(get_current_user)
):
    """
    Schedule a downgrade to take effect at end of current billing period.
    
    Does NOT call Dodo immediately. Stores intent in pending_plan_changes table.
    The webhook handler applies the change when the renewal event arrives.
    """
    user_id = user["db_user_id"]
    
    # Map target plan to product ID dynamically
    if body.target_plan == "creator":
        target_role = "creator"
        # Get the monthly creator product (downgrade typically goes to monthly)
        target_product = await dodo_service.get_product_by_role_and_interval(
            app_role="creator",
            billing_interval="monthly",
        )
        if not target_product:
            raise HTTPException(status_code=500, detail="Creator product not found")
        target_product_id = target_product["product_id"]
    elif body.target_plan == "free":
        # For free, we cancel at period end instead
        raise HTTPException(
            status_code=400, 
            detail="To downgrade to free, use the cancel endpoint instead"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid target plan")
    
    async with get_db_connection() as conn:
        # Get current subscription
        sub = await billing_queries.get_user_subscription(conn, user_id)
        
        if not sub:
            raise HTTPException(status_code=400, detail="No active subscription")
        
        if sub["status"] not in ("active", "trialing"):
            raise HTTPException(status_code=400, detail="Subscription not active")
        
        current_product_id = sub["product_id"]
        subscription_id = sub["subscription_id"]
        effective_at = sub.get("current_period_end")
        
        if not effective_at:
            raise HTTPException(status_code=400, detail="Cannot determine billing period end")
        
        # Check this is actually a downgrade (can't schedule "downgrade" to Pro from Creator)
        current_role = await billing_queries.get_role_for_product(conn, current_product_id)
        if current_role == target_role:
            raise HTTPException(status_code=400, detail="Already on this plan")
        
        # Create pending change
        change_id = await billing_queries.create_pending_plan_change(
            conn,
            user_id=user_id,
            subscription_id=subscription_id,
            current_product_id=current_product_id,
            target_product_id=target_product_id,
            target_role=target_role,
            effective_at=effective_at,
        )
    
    return {
        "status": "scheduled",
        "change_id": str(change_id),
        "target_plan": target_role,
        "effective_at": effective_at.isoformat(),
    }


@router.delete("/schedule-downgrade")
async def cancel_scheduled_downgrade(user: AuthUser = Depends(get_current_user)):
    """
    Cancel a scheduled downgrade.
    User changes their mind before the billing period ends.
    """
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        count = await billing_queries.cancel_pending_plan_changes(conn, user_id)
    
    if count == 0:
        raise HTTPException(status_code=404, detail="No pending downgrade to cancel")
    
    return {"status": "cancelled", "changes_cancelled": count}


@router.post("/cancel")
async def cancel_subscription(user: AuthUser = Depends(get_current_user)):
    """
    Cancel subscription at end of current billing period.
    User keeps access until period ends.
    """
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        sub = await billing_queries.get_user_subscription(conn, user_id)
        
        if not sub:
            raise HTTPException(status_code=400, detail="No active subscription")
        
        if sub["status"] not in ("active", "trialing", "on_hold"):
            raise HTTPException(status_code=400, detail="Subscription not active")
        
        subscription_id = sub["subscription_id"]
    
    # Call Dodo to set cancel_at_period_end flag
    try:
        result = await dodo_service.cancel_subscription(
            subscription_id=subscription_id,
            immediate=False,  # At period end
        )
        return {
            "status": "cancel_scheduled",
            "message": "Your subscription will be cancelled at the end of the current billing period.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.post("/reactivate")
async def reactivate_subscription(user: AuthUser = Depends(get_current_user)):
    """
    Reactivate a cancelled subscription (undo cancel_at_period_end).
    Only works if the subscription hasn't actually expired yet.
    """
    user_id = user["db_user_id"]
    
    async with get_db_connection() as conn:
        sub = await billing_queries.get_user_subscription(conn, user_id)
        
        if not sub:
            raise HTTPException(status_code=400, detail="No subscription found")
        
        if not sub.get("cancel_at_next_billing_date"):
            raise HTTPException(status_code=400, detail="Subscription is not set to cancel")
        
        subscription_id = sub["subscription_id"]
    
    # Call Dodo to clear cancel_at_period_end flag
    try:
        from app.services.dodo_client import get_dodo_client
        async with get_dodo_client() as client:
            await client.subscriptions.update(
                subscription_id,
                cancel_at_period_end=False,
            )
        
        return {
            "status": "reactivated",
            "message": "Your subscription will continue to renew.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to reactivate subscription")

