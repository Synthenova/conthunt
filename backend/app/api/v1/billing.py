"""Billing API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

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
        # Read persisted Dodo customer id from DB (token does not carry this field).
        dodo_customer_id = await billing_service.get_user_dodo_customer_id(user["db_user_id"])
        
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
    """Get canonical billing context used for UI + action gating."""
    return await billing_service.get_billing_context(user["db_user_id"])


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
        context = await billing_service.require_allowed_action(
            user["db_user_id"], billing_service.BILLING_ACTION_PREVIEW_CHANGE
        )
        subscription_id = context.get("subscription_id")
        if not subscription_id:
            raise HTTPException(status_code=400, detail="No active subscription found")
        
        preview = await dodo_client.preview_change_plan(
            subscription_id=subscription_id,
            product_id=request.target_product_id,
        )
        return preview
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reactivate")
async def reactivate_subscription(user: AuthUser = Depends(get_current_user)):
    """
    Get payment link to reactivate an on_hold subscription.
    The user is redirected to Dodo's payment page to update their payment method.
    Upon successful payment, the subscription is automatically reactivated.
    """
    from app.services import dodo_client
    from app.core import get_settings
    
    try:
        context = await billing_service.require_allowed_action(
            user["db_user_id"], billing_service.BILLING_ACTION_REACTIVATE
        )
        subscription_id = context.get("subscription_id")
        if not subscription_id:
            raise HTTPException(status_code=400, detail="No subscription found")
        
        settings = get_settings()
        result = await dodo_client.update_payment_method(
            subscription_id=subscription_id,
            return_url=settings.FRONTEND_RETURN_URL,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
