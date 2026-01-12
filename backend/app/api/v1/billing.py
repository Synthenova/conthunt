"""Billing API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.auth import get_current_user, AuthUser
from app.services import billing_service


router = APIRouter(prefix="/billing")


class CheckoutRequest(BaseModel):
    product_id: str


class PlanChangeRequest(BaseModel):
    target_product_id: str


@router.get("/products")
async def list_products():
    """List all available subscription plans."""
    products = await billing_service.get_products()
    return {"products": products}


@router.post("/checkout")
async def create_checkout(
    request: CheckoutRequest,
    user: AuthUser = Depends(get_current_user),
):
    """Create a checkout session for a product."""
    try:
        # Get dodo_customer_id if user has one
        dodo_customer_id = user.get("dodo_customer_id")
        
        session = await billing_service.create_checkout(
            user_id=user["db_user_id"],
            email=user.get("email", ""),
            product_id=request.product_id,
            dodo_customer_id=dodo_customer_id,
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscription")
async def get_subscription(user: AuthUser = Depends(get_current_user)):
    """Get current subscription and any pending plan changes."""
    subscription = await billing_service.get_user_subscription(user["db_user_id"])
    
    if not subscription:
        return {
            "has_subscription": False,
            "role": user.get("role", "free"),
        }
    
    # Use the role from DB (db_role) not from Firebase token
    db_role = subscription.pop("db_role", user.get("role", "free"))
    
    return {
        "has_subscription": True,
        "role": db_role,
        **subscription,
    }


@router.post("/preview-change")
async def preview_plan_change(
    request: PlanChangeRequest,
    user: AuthUser = Depends(get_current_user),
):
    """
    Preview plan change to see proration details before confirming.
    Shows credit/charge amount for the change.
    """
    from app.services import dodo_client
    
    try:
        subscription = await billing_service.get_user_subscription(user["db_user_id"])
        if not subscription:
            raise HTTPException(status_code=400, detail="No active subscription")
        
        preview = await dodo_client.preview_change_plan(
            subscription_id=subscription["subscription_id"],
            product_id=request.target_product_id,
        )
        return preview
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upgrade")
async def request_upgrade(
    request: PlanChangeRequest,
    user: AuthUser = Depends(get_current_user),
):
    """
    Request immediate upgrade to a higher plan.
    Charges prorated amount for remaining billing period.
    """
    try:
        result = await billing_service.request_upgrade(
            user_id=user["db_user_id"],
            target_product_id=request.target_product_id,
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/downgrade")
async def request_downgrade(
    request: PlanChangeRequest,
    user: AuthUser = Depends(get_current_user),
):
    """
    Request downgrade to a lower plan at end of billing cycle.
    Current access maintained until renewal.
    """
    try:
        result = await billing_service.request_downgrade(
            user_id=user["db_user_id"],
            target_product_id=request.target_product_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/downgrade")
async def cancel_downgrade(user: AuthUser = Depends(get_current_user)):
    """Cancel pending downgrade."""
    cancelled = await billing_service.cancel_pending_downgrade(user["db_user_id"])
    
    if cancelled:
        return {"message": "Pending downgrade cancelled"}
    else:
        return {"message": "No pending downgrade found"}


@router.post("/cancel")
async def request_cancel(user: AuthUser = Depends(get_current_user)):
    """
    Request subscription cancellation at end of billing period.
    Access maintained until period ends, then reverts to free tier.
    """
    try:
        result = await billing_service.request_cancel(user["db_user_id"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel")
async def undo_cancel(user: AuthUser = Depends(get_current_user)):
    """Undo scheduled cancellation."""
    try:
        result = await billing_service.undo_cancel(user["db_user_id"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
