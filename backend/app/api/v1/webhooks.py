"""Payment webhook endpoints (Dodo)."""
import hmac
import hashlib
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request
import base64
from sqlalchemy import text

from app.core import get_settings, logger
from app.db import get_db_connection, queries
from app.schemas.roles import UserRole

router = APIRouter(tags=["webhooks"])


def parse_dodo_signature_header(header: str) -> str | None:
    """Parse v1 signature from webhook header."""
    parts = header.split(",")
    for i in range(0, len(parts) - 1, 2):
        version = parts[i].strip()
        sig = parts[i + 1].strip()
        if version == "v1":
            return sig
    return None


def get_dodo_signing_key(raw_secret: str) -> bytes:
    """Decode Dodo webhook secret."""
    if not raw_secret:
        raise ValueError("Empty webhook secret")
    if raw_secret.startswith("whsec_"):
        return base64.b64decode(raw_secret[6:])
    return raw_secret.encode("utf-8")


def verify_dodo_webhook(
    raw_body: bytes, 
    webhook_id: str, 
    webhook_timestamp: str, 
    webhook_signature: str
) -> None:
    """Verify webhook signature."""
    settings = get_settings()
    raw_secret = settings.DODO_WEBHOOK_SECRET

    if not raw_secret:
        logger.warning("DODO_WEBHOOK_SECRET not configured, skipping verification")
        return

    try:
        key = get_dodo_signing_key(raw_secret)
    except Exception as e:
        logger.error(f"Failed to parse Dodo webhook secret: {e}")
        raise HTTPException(status_code=500, detail="Webhook secret misconfigured")

    received_sig_b64 = parse_dodo_signature_header(webhook_signature)
    if not received_sig_b64:
        raise HTTPException(status_code=400, detail="Signature parsing error")

    try:
        payload_str = raw_body.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid body encoding")

    signed_message = f"{webhook_id}.{webhook_timestamp}.{payload_str}".encode("utf-8")
    digest = hmac.new(key, signed_message, hashlib.sha256).digest()
    expected_sig_b64 = base64.b64encode(digest).decode("ascii")

    if not hmac.compare_digest(expected_sig_b64, received_sig_b64):
        logger.error("Webhook signature mismatch!")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


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
    
    webhook_id = request.headers.get("webhook-id")
    webhook_ts = request.headers.get("webhook-timestamp")
    webhook_sig = request.headers.get("webhook-signature")

    if not webhook_id or not webhook_ts or not webhook_sig:
        raise HTTPException(status_code=400, detail="Missing webhook headers")

    verify_dodo_webhook(raw_body, webhook_id, webhook_ts, webhook_sig)

    event = await request.json()
    event_type = event.get("type")
    data = event.get("data", {})
    
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
