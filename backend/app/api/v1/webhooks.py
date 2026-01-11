from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text
from sqlalchemy import text

from app.core import get_settings, logger
from app.db import get_db_connection, queries
from app.schemas.roles import UserRole

router = APIRouter(tags=["webhooks"])





def parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


@router.post("/webhooks/dodo/subscription")
async def dodo_subscription_webhook(request: Request):
    """
    Handle Dodo payment webhooks.
    
    Expects user_id in metadata (passed during checkout).
    Events handled:
    - subscription.active / subscription.renewed: Grant access, set period_start
    - subscription.plan_changed: Update role
    - subscription.cancelled / subscription.expired: Revoke access
    - subscription.on_hold: Keep access (grace period)
    - payment.failed: Keep access, log warning
    
    """
    raw_body = await request.body()
    
    # Extract headers
    webhook_id = request.headers.get("webhook-id")
    webhook_sig = request.headers.get("webhook-signature")
    webhook_ts = request.headers.get("webhook-timestamp")

    if not webhook_id or not webhook_sig or not webhook_ts:
         raise HTTPException(status_code=400, detail="Missing webhook headers")

    from app.services.dodo_client import get_dodo_client
    from dodopayments import AsyncDodoPayments
    
    try:
        webhook_key = get_settings().DODO_WEBHOOK_SECRET
        if not webhook_key:
             logger.warning("DODO_WEBHOOK_SECRET not configured, skipping verification")
             return {"status": "ignored", "reason": "missing_webhook_secret"}

        settings = get_settings()
        # Webhook verification doesn't need async, but we use the client structure
        client = AsyncDodoPayments(
            bearer_token=settings.DODO_API_KEY,
            environment="test_mode" if "test" in settings.DODO_BASE_URL else "live_mode",
            webhook_key=webhook_key
        )

        event = client.webhooks.unwrap(
            raw_body,
            headers={
                "webhook-id": webhook_id,
                "webhook-signature": webhook_sig,
                "webhook-timestamp": webhook_ts,
            },
        )
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 1) Event type
    event_type = event.type

    # 2) Event payload
    # event.data is typically a Pydantic model -> convert once if you want a dict
    data = event.data.model_dump() if hasattr(event.data, "model_dump") else event.data
    
    logger.info(f"Dodo webhook: {event_type} (ID: {webhook_id})")
    
    # Extract user_id from metadata (we pass this during checkout)
    metadata = data.get("metadata") or {}
    customer = data.get("customer") or {}
    customer_metadata = customer.get("metadata") or {}
    customer_id = customer.get("customer_id") or data.get("customer_id")
    
    user_id_str = metadata.get("user_id") or customer_metadata.get("user_id")
    
    if not user_id_str:
        logger.warning(f"Webhook {webhook_id}: user_id missing in metadata. Skipping.")
        return {"status": "ignored", "reason": "missing_user_id"}
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        logger.error(f"Webhook {webhook_id}: Invalid user_id format: {user_id_str}")
        return {"status": "ignored", "reason": "invalid_user_id"}
    
    subscription_id = data.get("subscription_id") or data.get("id")
    product_id = data.get("product_id")
    status = data.get("status")
    current_period_start = parse_iso_datetime(data.get("current_period_start"))
    
    # Map product to role
    settings = get_settings()
    product_role_map = {
        settings.DODO_PRODUCT_CREATOR: UserRole.CREATOR.value,
        settings.DODO_PRODUCT_PRO: UserRole.PRO_RESEARCH.value,
    }
    current_product_role = product_role_map.get(product_id)
    
    logger.info(
        f"Webhook {webhook_id}: user_id={user_id}, type={event_type}, "
        f"status={status}, role={current_product_role}"
    )

    new_role = None
    should_clear = False

    if event_type in ("subscription.active", "subscription.renewed", "subscription.plan_changed"):
        if status in ("active", "trialing") and current_product_role:
            new_role = current_product_role

    elif event_type in ("subscription.cancelled", "subscription.expired"):
        should_clear = True
        logger.info(f"Webhook {webhook_id}: Subscription ended.")

    elif event_type == "subscription.on_hold":
        logger.warning(f"Webhook {webhook_id}: On hold. Access preserved.")

    elif event_type == "payment.failed":
        logger.warning(f"Webhook {webhook_id}: Payment failed. Access preserved.")

    # Update DB
    async with get_db_connection() as conn:
        if should_clear:
            await queries.clear_user_subscription(conn, user_id)
        else:
            await queries.update_user_subscription(
                conn=conn,
                user_id=user_id,
                role=new_role,
                customer_id=customer_id,
                subscription_id=subscription_id,
                current_period_start=current_period_start,
            )
        
        # Sync Firebase claims if role changed
        if new_role or should_clear:
            try:
                from firebase_admin import auth
                result = await conn.execute(
                    text("SELECT firebase_uid FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                row = result.fetchone()
                if row:
                    final_role = "free" if should_clear else new_role
                    auth.set_custom_user_claims(row[0], {
                        "role": final_role,
                        "db_user_id": str(user_id)
                    })
                    logger.info(f"Synced Firebase claims: user_id={user_id} -> role={final_role}")
            except Exception as e:
                logger.error(f"Failed to sync Firebase claims: {e}")

    return {"status": "processed"}
