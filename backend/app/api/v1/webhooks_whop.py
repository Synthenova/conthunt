"""Whop Webhook Handler."""
from fastapi import APIRouter, Request, HTTPException

import base64
from whop_sdk import Whop
from firebase_admin import auth as fb_auth

from app.core import settings, logger
from app.db import get_db_connection
from sqlalchemy import text

router = APIRouter(prefix="/webhooks/whop", tags=["webhooks"])

# Get settings instance
app_settings = settings.get_settings()

# Use Sync Whop Client for Webhooks because 'unwrap' (signature verification) 
# is currently only available on the Sync WebhooksResource in the SDK.
whop_client = Whop(
    api_key=app_settings.WHOP_API_KEY,
    app_id=getattr(app_settings, "WHOP_APP_ID", None),
    webhook_key=base64.b64encode(app_settings.WHOP_WEBHOOK_SECRET.encode()).decode() if app_settings.WHOP_WEBHOOK_SECRET else None
)

async def process_membership_role(whop_user_id: str, product_id: str, action: str):
    """
    Update user role based on membership event.
    """
    logger.info(f"Whop Webhook: Processing {action} for {whop_user_id} (Product: {product_id})")
    
    async with get_db_connection() as conn:
        role = "free"
        if action == "activate":
            if product_id == app_settings.WHOP_PRODUCT_PRO:
                role = "pro_research"
            elif product_id == app_settings.WHOP_PRODUCT_CREATOR:
                role = "creator"
            else:
                logger.debug(f"Whop Webhook: Unknown product {product_id}, skipping.")
                return 

        if action == "deactivate":
            role = "free"

        if action == "activate":
             logger.info(f"DB PRE-OP: Webhook Update (Activate) -> whop_id={whop_user_id}, role={role}")
             result = await conn.execute(
                 text("UPDATE users SET role = :role WHERE whop_user_id = :wuid RETURNING id"),
                 {"role": role, "wuid": whop_user_id}
             )
             if result.rowcount > 0:
                 logger.info(f"Whop Webhook: Updated {whop_user_id} to {role}")
             else:
                 logger.warning(f"Whop Webhook: User {whop_user_id} not found for update")
                 
        elif action == "deactivate":
            logger.info(f"DB PRE-OP: Webhook Update (Deactivate/Downgrade) -> whop_id={whop_user_id}, role=free")
            await conn.execute(
                text("UPDATE users SET role = 'free' WHERE whop_user_id = :wuid"),
                {"wuid": whop_user_id}
            )
            logger.info(f"Whop Webhook: Downgraded {whop_user_id} to free")

        # Fetch db_user_id for claims (if available)
        db_user_id = None
        try:
            result = await conn.execute(
                text("SELECT id FROM users WHERE whop_user_id = :wuid"),
                {"wuid": whop_user_id}
            )
            row = result.fetchone()
            if row:
                db_user_id = str(row[0])
        except Exception as e:
            logger.warning(f"Whop Webhook: Failed to fetch db_user_id for {whop_user_id}: {e}")

        await conn.commit()

    # Update Firebase custom claims so auth reflects the latest role.
    firebase_uid = f"whop:{whop_user_id}"
    try:
        existing_claims = {}
        try:
            user = fb_auth.get_user(firebase_uid)
            existing_claims = user.custom_claims or {}
        except fb_auth.UserNotFoundError:
            logger.warning(f"Whop Webhook: Firebase user not found for {firebase_uid}")

        updated_claims = {
            **existing_claims,
            "role": role,
            "auth_provider": "whop",
        }
        if db_user_id:
            updated_claims["db_user_id"] = db_user_id

        fb_auth.set_custom_user_claims(firebase_uid, updated_claims)
        logger.info(f"Whop Webhook: Updated Firebase claims for {firebase_uid} to role={role}")
    except Exception as e:
        logger.warning(f"Whop Webhook: Failed to update Firebase claims for {firebase_uid}: {e}")

@router.post("")
async def handle_webhook(req: Request):
    """
    Handle Whop Webhooks using SDK.
    """
    raw_body = await req.body()
    headers = dict(req.headers)
    
    try:
        # SDK requires headers as a keyword argument!
        webhook_data = whop_client.webhooks.unwrap(raw_body.decode("utf-8"), headers=headers)
    except Exception as e:
        logger.error(f"Whop Webhook Verification Failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_type = webhook_data.type 
    logger.info(f"Whop Webhook Verified: {event_type}")

    try:
        # Safely extract user_id and product_id from event data
        event_data = webhook_data.data
        
        def get_attr(obj, path):
            parts = path.split('.')
            curr = obj
            for p in parts:
                if isinstance(curr, dict):
                    curr = curr.get(p)
                else:
                    curr = getattr(curr, p, None)
                if curr is None: return None
            return curr

        whop_user_id = get_attr(event_data, "user.id")
        product_id = get_attr(event_data, "product.id")
        logger.info(f"Whop Webhook: User ID: {whop_user_id}, Product ID: {product_id}")
        if not whop_user_id:
             logger.debug("Whop Webhook ignored: No user ID found.")
             return {"ok": True}

        if event_type == "membership.activated":
            await process_membership_role(whop_user_id, product_id, "activate")
        elif event_type == "membership.deactivated":
             await process_membership_role(whop_user_id, product_id, "deactivate")

    except Exception as e:
        logger.error(f"Whop Webhook Processing Error: {e}")
         
    return {"ok": True}
