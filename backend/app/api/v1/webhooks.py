"""Payment webhook endpoints (Dodo)."""
import hmac
import hashlib
from fastapi import APIRouter, Header, HTTPException, Request
import base64

from app.core import get_settings, logger
from app.db import get_db_connection, queries
from app.schemas.roles import UserRole

router = APIRouter(tags=["webhooks"])


def parse_dodo_signature_header(header: str) -> str:
    """
    Header may contain multiple comma-separated pieces, e.g.:
      "v1,abcde12345"
      "v1,abcde12345,v0,oldsig"
    Return the base64 signature part for version "v1".
    """
    parts = header.split(",")
    for i in range(0, len(parts) - 1, 2):
        version = parts[i].strip()
        sig = parts[i + 1].strip()
        if version == "v1":
            return sig
    return None


def get_dodo_signing_key(raw_secret: str) -> bytes:
    """
    Dodo uses Standard Webhooks:
    secret is base64-encoded and prefixed with 'whsec_'.
    We must base64-decode the part after 'whsec_' to get the real key.
    
    """
    if not raw_secret:
        raise ValueError("Empty webhook secret")

    if raw_secret.startswith("whsec_"):
        b64_part = raw_secret[len("whsec_") :]
        return base64.b64decode(b64_part)
    # fallback: treat as raw bytes (just in case)
    return raw_secret.encode("utf-8")


def verify_dodo_webhook(raw_body: bytes, webhook_id: str, webhook_timestamp: str, webhook_signature: str) -> None:
    settings = get_settings()
    raw_secret = settings.DODO_WEBHOOK_SECRET

    logger.info("Dodo webhook headers: %s", {
        "webhook-id": webhook_id,
        "webhook-timestamp": webhook_timestamp,
        "webhook-signature": webhook_signature,
    })

    if not raw_secret:
        logger.warning("DODO_WEBHOOK_SECRET not configured, skipping verification")
        return  # only for dev

    try:
        key = get_dodo_signing_key(raw_secret)
    except Exception as e:
        logger.error(f"Failed to parse Dodo webhook secret: {e}")
        raise HTTPException(status_code=500, detail="Webhook secret misconfigured")

    # Parse header → get v1 base64 signature
    received_sig_b64 = parse_dodo_signature_header(webhook_signature)
    if not received_sig_b64:
        logger.error("No v1 signature found in webhook-signature header")
        raise HTTPException(status_code=400, detail="Signature parsing error")

    # Build signed_message = "{webhook-id}.{webhook-timestamp}.{raw_payload}"
    try:
        payload_str = raw_body.decode("utf-8")
    except UnicodeDecodeError:
        logger.error("Failed to decode webhook body as utf-8")
        raise HTTPException(status_code=400, detail="Invalid body encoding")

    signed_message = f"{webhook_id}.{webhook_timestamp}.{payload_str}".encode("utf-8")

    # HMAC-SHA256 using the DECODED secret key, then base64-encode
    digest = hmac.new(key, signed_message, hashlib.sha256).digest()
    expected_sig_b64 = base64.b64encode(digest).decode("ascii")

    if not hmac.compare_digest(expected_sig_b64, received_sig_b64):
        logger.error("Webhook signature mismatch!")
        logger.error(f"Expected (b64): {expected_sig_b64}")
        logger.error(f"Received (b64): {received_sig_b64}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


@router.post("/webhooks/dodo/subscription")
async def dodo_subscription_webhook(request: Request):
    """
    Handle Dodo payment webhooks.
    
    Verified events:
    - subscription.active: Update role to creator/pro based on product_id
    - subscription.plan_changed: Update role
    - subscription.cancelled / payment.failed: Determine status (could downgrade)
    """
    raw_body = await request.body()
    
    # Extract headers
    webhook_id = request.headers.get("webhook-id")
    webhook_ts = request.headers.get("webhook-timestamp")
    webhook_sig = request.headers.get("webhook-signature")

    if not webhook_id or not webhook_ts or not webhook_sig:
        raise HTTPException(status_code=400, detail="Missing webhook headers")

    # Verify signature
    try:
        verify_dodo_webhook(raw_body, webhook_id, webhook_ts, webhook_sig)
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise

    # Parse payload
    event = await request.json()
    event_type = event.get("type")
    data = event.get("data", {})
    
    logger.info(f"Received Dodo webhook: {event_type} (ID: {webhook_id})")
    
    # Extract data for updates
    # Hierarchy: data -> customer -> metadata keys
    metadata = data.get("metadata") or {}
    customer = data.get("customer") or {}
    customer_metadata = customer.get("metadata") or {}
    customer_id = customer.get("customer_id") or data.get("customer_id")
    
    # Firebase UID should be in metadata
    firebase_uid = metadata.get("firebase_uid") or customer_metadata.get("firebase_uid")
    
    if not firebase_uid:
        logger.warning(f"Webhook {webhook_id}: firebase_uid missing in metadata. Skipping role update.")
        return {"status": "ignored", "reason": "missing_uid"}
        
    subscription_id = data.get("subscription_id") or data.get("id")
    product_id = data.get("product_id")
    status = data.get("status")
    
    # Determine new role based on Event + Status + Product Matrix
    settings = get_settings()
    current_product_role = None
    
    # Map product to role
    if product_id == settings.DODO_PRODUCT_CREATOR:
        current_product_role = UserRole.CREATOR.value
    elif product_id == settings.DODO_PRODUCT_PRO:
        current_product_role = UserRole.PRO_RESEARCH.value
    
    new_role = None
    
    # Log the context for debugging
    logger.info(f"Processing webhook {webhook_id}: Type={event_type}, Status={status}, Product={product_id}, MappedRole={current_product_role}")

    # Matrix Logic:
    
    # 1. Active States: Grant Access
    if event_type in ("subscription.active", "subscription.renewed", "subscription.plan_changed"):
        if status in ("active", "trialing") and current_product_role:
             new_role = current_product_role
        else:
            # e.g. plan changed but status is past_due? Keep existing role (do nothing)
            logger.info(f"Webhook {webhook_id}: Active event but status '{status}' or unknown product. No role change.")

    # 2. Cancellation / Expiration: Revoke Access
    elif event_type in ("subscription.cancelled", "subscription.expired"):
        # Immediate downgrade
        new_role = "free"
        logger.info(f"Webhook {webhook_id}: Subscription cancelled/expired. Downgrading to free.")

    # 3. Failures / Past Due: Persist Access (Validation Grace)
    elif event_type in ("payment.failed",):
        # Do not change role. Log warning.
        logger.warning(f"Webhook {webhook_id}: Payment failed. Keeping existing access for now.")
        new_role = None
        
    else:
        # Unknown event type
        logger.info(f"Webhook {webhook_id}: Unhandled event type {event_type}. No role change.")
        
    # Update DB
    async with get_db_connection() as conn:
        success = await queries.update_user_dodo_subscription(
            conn=conn,
            firebase_uid=firebase_uid,
            role=new_role,  # Only updates if not None
            customer_id=customer_id,
            subscription_id=subscription_id,
            product_id=product_id,
            status=status,
        )
        
        if success:
            logger.info(f"Updated user {firebase_uid} Dodo state: {status}, Role: {new_role}")
            
            # Sync to Firebase custom claims if role changed
            if new_role:
                try:
                    from firebase_admin import auth
                    auth.set_custom_user_claims(firebase_uid, {"role": new_role})
                    logger.info(f"Synced Firebase claims for {firebase_uid}")
                except Exception as e:
                    logger.error(f"Failed to sync Firebase claims: {e}")
        else:
            logger.warning(f"User {firebase_uid} not found for webhook update")

    return {"status": "processed"}
