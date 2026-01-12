"""Dodo Payments webhook handler.

Implements idempotent "single sync" pattern:
- Every subscription event goes through sync_subscription_snapshot()
- Deduplication via webhook_id
- Out-of-order protection via event timestamps
- Dynamic product → role mapping via dodo_products table
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from app.core import get_settings, logger
from app.db import get_db_connection
from app.db.queries import billing as billing_queries
from app.db.queries.users import update_user_subscription
from app.schemas.roles import UserRole
from app.services.dodo_client import dodo_service

router = APIRouter(tags=["webhooks"])


# ============================================================================
# HELPERS
# ============================================================================

def now_utc() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string from Dodo."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def is_entitled_status(status: str | None) -> bool:
    """
    Determine if subscription status grants access.
    
    - active: Normal paid access
    - trialing: Trial period access
    - on_hold: Payment failed, but we still grant access (grace period per spec)
    """
    return status in {"active", "trialing", "on_hold"}


async def resolve_user_id(
    conn,
    *,
    metadata: dict,
    customer_id: str | None,
    subscription_id: str | None,
) -> UUID | None:
    """
    Resolve internal user_id from webhook payload.
    
    Priority:
    1. metadata.user_id (passed during checkout)
    2. Lookup by subscription_id in user_subscriptions
    3. Lookup by customer_id in users table
    """
    # Primary: metadata.user_id
    user_id_str = (metadata or {}).get("user_id")
    if user_id_str:
        try:
            return UUID(user_id_str)
        except ValueError:
            pass
    
    # Fallback 1: by subscription_id
    if subscription_id:
        user_id = await billing_queries.get_user_id_by_subscription(conn, subscription_id)
        if user_id:
            return user_id
    
    # Fallback 2: by customer_id
    if customer_id:
        user_id = await billing_queries.get_user_id_by_customer(conn, customer_id)
        if user_id:
            return user_id
    
    return None


async def sync_firebase_claims(conn, user_id: UUID, role: str) -> None:
    """Sync role to Firebase custom claims."""
    try:
        from firebase_admin import auth
        
        result = await conn.execute(
            text("SELECT firebase_uid FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        row = result.fetchone()
        if row and row[0]:
            auth.set_custom_user_claims(row[0], {
                "role": role,
                "db_user_id": str(user_id),
            })
            logger.info(f"Synced Firebase claims: user_id={user_id} → role={role}")
    except Exception as e:
        logger.error(f"Failed to sync Firebase claims for {user_id}: {e}")


# ============================================================================
# MAIN SYNC FUNCTION
# ============================================================================

async def sync_subscription_snapshot(
    conn,
    *,
    webhook_id: str,
    event_type: str,
    event_ts: datetime,
    sub: dict,
) -> dict:
    """
    The ONE function: derive DB state from the subscription snapshot.
    
    Does NOT branch on event_type — treats every webhook as a state sync.
    """
    result = {"action": "none", "user_id": None}
    
    # Only process subscription payloads
    payload_type = sub.get("payload_type")
    if payload_type and payload_type != "Subscription":
        logger.info(f"[{webhook_id}] Skipping non-subscription payload: {payload_type}")
        return {"action": "skipped", "reason": "non_subscription_payload"}
    
    # Extract fields from snapshot
    subscription_id = sub.get("subscription_id")
    product_id = sub.get("product_id")
    status = sub.get("status")
    cancel_at_next_billing_date = bool(sub.get("cancel_at_next_billing_date"))
    cancelled_at = parse_iso_datetime(sub.get("cancelled_at"))
    expires_at = parse_iso_datetime(sub.get("expires_at"))
    
    # Dodo uses previous_billing_date / next_billing_date
    current_period_start = parse_iso_datetime(sub.get("previous_billing_date"))
    current_period_end = parse_iso_datetime(sub.get("next_billing_date"))
    
    # Customer info
    customer = sub.get("customer") or {}
    customer_id = customer.get("customer_id") or sub.get("customer_id")
    metadata = sub.get("metadata") or {}
    customer_metadata = customer.get("metadata") or {}
    
    # Merge metadata (subscription metadata takes priority)
    merged_metadata = {**customer_metadata, **metadata}
    
    # Resolve user
    user_id = await resolve_user_id(
        conn,
        metadata=merged_metadata,
        customer_id=customer_id,
        subscription_id=subscription_id,
    )
    
    if not user_id:
        logger.warning(f"[{webhook_id}] Could not resolve user_id; skipping")
        return {"action": "skipped", "reason": "no_user_id"}
    
    result["user_id"] = user_id
    
    if not subscription_id or not product_id:
        logger.warning(f"[{webhook_id}] Missing subscription_id/product_id; skipping")
        return {"action": "skipped", "reason": "missing_ids"}
    
    # Out-of-order protection
    last_event_ts = await billing_queries.get_last_event_ts(conn, subscription_id)
    if last_event_ts and event_ts <= last_event_ts:
        logger.info(f"[{webhook_id}] Stale event (event_ts={event_ts} <= last={last_event_ts}); skipping")
        return {"action": "skipped", "reason": "stale_event"}
    
    # Get previous state for credit logic
    old_subscription = await billing_queries.get_subscription_by_id(conn, subscription_id)
    
    # Ensure product is cached (for role lookup)
    await dodo_service.ensure_product_cached(conn, product_id)
    
    # Get role from product metadata
    role_from_plan = await billing_queries.get_role_for_product(conn, product_id)
    
    # Determine final role
    entitled_now = is_entitled_status(status)
    if entitled_now and role_from_plan:
        final_role = role_from_plan
    else:
        final_role = UserRole.FREE.value
    
    # Upsert normalized subscription record
    await billing_queries.upsert_user_subscription(
        conn,
        user_id=user_id,
        subscription_id=subscription_id,
        customer_id=customer_id,
        product_id=product_id,
        status=status,
        cancel_at_next_billing_date=cancel_at_next_billing_date,
        cancelled_at=cancelled_at,
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        expires_at=expires_at,
        event_ts=event_ts,
    )
    
    # Mirror to users table (for backward compatibility + quick lookups)
    await update_user_subscription(
        conn,
        user_id=user_id,
        role=final_role,
        customer_id=customer_id,
        subscription_id=subscription_id,
        current_period_start=current_period_start,
    )
    
    result["action"] = "synced"
    result["role"] = final_role
    result["status"] = status
    
    # =========================================================================
    # CREDIT HOOKS
    # =========================================================================
    # Detect lifecycle events and trigger credit operations
    
    new_subscription = await billing_queries.get_subscription_by_id(conn, subscription_id)
    
    if old_subscription and new_subscription:
        old_period_start = old_subscription.get("current_period_start")
        new_period_start = new_subscription.get("current_period_start")
        old_product_id = old_subscription.get("product_id")
        new_product_id = new_subscription.get("product_id")
        
        # Detect RENEWAL: period_start changed
        if old_period_start and new_period_start and old_period_start != new_period_start:
            logger.info(f"[{webhook_id}] Renewal detected: {old_period_start} → {new_period_start}")
            result["credit_event"] = "renewal"
            
            # Check for pending downgrade to apply
            pending = await billing_queries.get_pending_changes_to_apply(conn, subscription_id)
            if pending and pending["status"] == "pending":
                logger.info(f"[{webhook_id}] Applying pending downgrade to {pending['target_product_id']}")
                try:
                    # Call Dodo API to change plan
                    await dodo_service.change_plan(
                        subscription_id=subscription_id,
                        new_product_id=pending["target_product_id"],
                        proration_mode="difference_immediately",
                    )
                    await billing_queries.mark_pending_change_applied(conn, pending["id"])
                    result["pending_change_applied"] = pending["id"]
                except Exception as e:
                    logger.error(f"[{webhook_id}] Failed to apply pending downgrade: {e}")
            
            # TODO: Grant full cycle credits here
            # await credit_tracker.on_renewal(user_id, final_role, new_period_start)
        
        # Detect UPGRADE: product changed within same period
        elif old_product_id and new_product_id and old_product_id != new_product_id:
            if old_period_start == new_period_start:
                logger.info(f"[{webhook_id}] Upgrade detected: {old_product_id} → {new_product_id}")
                result["credit_event"] = "upgrade"
                
                # TODO: Grant top-up credits here (Option A)
                # await credit_tracker.on_upgrade(user_id, old_product_id, new_product_id)
    
    elif not old_subscription and new_subscription:
        # New subscription
        logger.info(f"[{webhook_id}] New subscription created")
        result["credit_event"] = "new_subscription"
        
        # TODO: Grant initial cycle credits here
        # await credit_tracker.on_new_subscription(user_id, final_role, current_period_start)
    
    # Sync Firebase claims
    await sync_firebase_claims(conn, user_id, final_role)
    
    return result


# ============================================================================
# WEBHOOK ENDPOINT
# ============================================================================

@router.post("/webhooks/dodo/subscription")
async def dodo_subscription_webhook(request: Request):
    """
    Handle Dodo subscription webhooks.
    
    Uses idempotent "single sync" pattern:
    - Deduplicates by webhook_id
    - Protects against out-of-order events
    - Derives state from subscription snapshot (not event type)
    """
    raw_body = await request.body()
    
    # Extract headers
    webhook_id = request.headers.get("webhook-id")
    webhook_sig = request.headers.get("webhook-signature")
    webhook_ts = request.headers.get("webhook-timestamp")
    
    if not webhook_id:
        raise HTTPException(status_code=400, detail="Missing webhook-id header")
    
    if not webhook_sig or not webhook_ts:
        raise HTTPException(status_code=400, detail="Missing webhook headers")
    
    # Verify signature
    settings = get_settings()
    webhook_key = settings.DODO_WEBHOOK_SECRET
    
    if not webhook_key:
        logger.warning("DODO_WEBHOOK_SECRET not configured, skipping verification")
        return {"status": "ignored", "reason": "missing_webhook_secret"}
    
    try:
        from dodopayments import AsyncDodoPayments
        
        client = AsyncDodoPayments(
            bearer_token=settings.DODO_API_KEY,
            environment="test_mode" if "test" in settings.DODO_BASE_URL else "live_mode",
            webhook_key=webhook_key,
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
    
    # Extract event data
    event_type = event.type
    event_ts = parse_iso_datetime(getattr(event, "timestamp", None)) or now_utc()
    sub = event.data.model_dump() if hasattr(event.data, "model_dump") else dict(event.data)
    subscription_id = sub.get("subscription_id")
    
    logger.info(f"[{webhook_id}] Received {event_type} for subscription {subscription_id}")
    
    async with get_db_connection() as conn:
        # Dedupe by webhook_id
        inserted = await billing_queries.upsert_webhook_event(
            conn,
            webhook_id=webhook_id,
            event_type=event_type,
            event_ts=event_ts,
            subscription_id=subscription_id,
            payload=sub,
        )
        
        if not inserted:
            logger.info(f"[{webhook_id}] Already processed (deduped)")
            return {"status": "ok", "deduped": True}
        
        try:
            # Sync subscription state
            result = await sync_subscription_snapshot(
                conn,
                webhook_id=webhook_id,
                event_type=event_type,
                event_ts=event_ts,
                sub=sub,
            )
            
            # Mark as processed
            await billing_queries.mark_webhook_processed(conn, webhook_id, status="ok")
            
            logger.info(f"[{webhook_id}] Processed: {result}")
            return {"status": "ok", **result}
            
        except Exception as e:
            logger.exception(f"[{webhook_id}] Sync failed: {e}")
            await billing_queries.mark_webhook_processed(
                conn,
                webhook_id,
                status="error",
                error=str(e),
            )
            raise HTTPException(status_code=500, detail="Webhook processing failed")
