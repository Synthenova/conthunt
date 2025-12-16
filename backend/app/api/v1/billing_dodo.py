"""Billing API dodo endpoints."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user, AuthUser
from app.core import get_settings
from app.services.dodo_client import dodo_client

router = APIRouter(prefix="/billing/dodo", tags=["billing"])


class CreateCheckoutBody(BaseModel):
    """Checkout session request."""
    plan: Literal["creator", "pro_research"]


@router.post("/checkout-session")
async def create_checkout_session(
    body: CreateCheckoutBody, 
    user: AuthUser = Depends(get_current_user)
):
    """
    Create a Dodo Checkout Session.
    Returns checkout_url to redirect the user to.
    """
    settings = get_settings()
    
    if body.plan == "creator":
        product_id = settings.DODO_PRODUCT_CREATOR
    elif body.plan == "pro_research":
        product_id = settings.DODO_PRODUCT_PRO
    else:
        raise HTTPException(status_code=400, detail="Invalid plan")

    # In test mode, we might want to validate DODO_API_KEY is present
    if not settings.DODO_API_KEY:
        raise HTTPException(status_code=500, detail="Payment configuration missing (API Key)")

    try:
        session = await dodo_client.create_checkout_session(
            product_id=product_id, 
            firebase_uid=user["uid"]
        )
        return {
            "checkout_url": session["checkout_url"], 
            "session_id": session["session_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session")
