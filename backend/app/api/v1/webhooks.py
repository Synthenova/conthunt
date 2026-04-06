"""Webhook handlers for Dodo Payments."""
import json
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

from app.core import logger
from app.integrations.posthog_client import capture_event_with_error
from app.services import dodo_client, billing_service
from app.services.telemetry_events import emit_payment_confirmed, emit_payment_webhook_received


router = APIRouter(prefix="/webhooks")


@router.post("/dodo")
async def handle_dodo_webhook(request: Request):
    """
    Handle all Dodo webhook events.
    Uses subscription.updated as primary sync for state changes.
    """
    # Get raw body and headers
    body = await request.body()
    headers = {
        "webhook-id": request.headers.get("webhook-id", ""),
        "webhook-signature": request.headers.get("webhook-signature", ""),
        "webhook-timestamp": request.headers.get("webhook-timestamp", ""),
    }
    
    # Verify signature using Dodo SDK
    try:
        client = dodo_client.get_dodo_client()
        event = client.webhooks.unwrap(body, headers=headers)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
    webhook_id = headers["webhook-id"]
    event_type = event.type
    event_data = event.data
    event_ts = getattr(event, 'timestamp', None) or datetime.utcnow()
    try:
        raw_payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raw_payload = {"type": event_type}
    
    
    logger.info(f"Received webhook: {event_type} (id: {webhook_id})")

    # Get subscription_id if available
    subscription_id = getattr(event_data, 'subscription_id', None)
    emit_payment_webhook_received(
        user_id=None,
        event_type=event_type,
        subject_id=subscription_id,
    )
    
    # Durable inbox + idempotency
    is_new = await billing_service.record_webhook_inbox_event(
        webhook_id=webhook_id,
        event_type=event_type,
        subscription_id=subscription_id,
        payload=raw_payload,
        event_ts=event_ts,
    )
    if not is_new:
        logger.info(f"Webhook {webhook_id} already processed, skipping")
        return {"status": "already_processed"}
    
    try:
        # Route by event type
        if event_type == "subscription.active":
            await handle_subscription_active(event_data, event_ts)
            
        elif event_type == "subscription.updated":
            await handle_subscription_updated(event_data, event_ts)
            
        elif event_type == "subscription.renewed":
            await handle_subscription_renewed(event_data, event_ts)
            
        elif event_type == "subscription.plan_changed":
            await handle_subscription_plan_changed(event_data, event_ts)
            
        elif event_type == "subscription.cancelled":
            await handle_subscription_cancelled(event_data, event_ts)
            
        elif event_type == "subscription.expired":
            await handle_subscription_expired(event_data, event_ts)
            
        elif event_type == "subscription.on_hold":
            await handle_subscription_on_hold(event_data, event_ts)

        elif event_type == "subscription.failed":
            await handle_subscription_failed(event_data, event_ts)

        elif event_type == "payment.succeeded":
            await handle_payment_succeeded(event_data)

        elif event_type == "payment.failed":
            await handle_payment_failed(event_data)

        elif event_type == "payment.processing":
            await handle_payment_processing(event_data)

        elif event_type == "payment.cancelled":
            await handle_payment_cancelled(event_data)
            
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")

        await billing_service.mark_webhook_inbox_status(webhook_id, "processed")
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook {webhook_id}: {e}")
        await billing_service.mark_webhook_inbox_status(webhook_id, "failed", str(e))
        capture_event_with_error(
            distinct_id="system:webhook_dodo",
            event="payment_webhook_failed",
            exception=e,
            properties={
                "event_type": event_type,
                "subscription_id": subscription_id,
                "success": False,
                "source": "webhook_dodo",
            },
        )
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def handle_subscription_active(data, event_ts: datetime):
    """
    Handle new subscription activation.
    Links user to subscription, sets role and credits.
    """
    subscription_id = data.subscription_id
    customer_id = data.customer.customer_id
    product_id = data.product_id
    metadata = data.metadata or {}
    
    logger.info(f"Processing subscription.active: sub={subscription_id}, customer={customer_id}, product={product_id}")
    
    # Find user - first try metadata, then customer_id
    user_id = await billing_service.find_user_by_metadata(metadata)
    if not user_id:
        user_id = await billing_service.find_user_by_customer_id(customer_id)
    
    if not user_id:
        logger.error(f"Could not find user for subscription {subscription_id}")
        return
    
    # New subscription activation sets the initial credit period start.
    await billing_service.apply_subscription_state(
        user_id=user_id,
        subscription_id=subscription_id,
        customer_id=customer_id,
        product_id=product_id,
        status="active",
        cancel_at_period_end=data.cancel_at_next_billing_date,
        current_period_start=data.previous_billing_date,
        current_period_end=data.next_billing_date,
        webhook_ts=event_ts,
        is_new_subscription=True,
    )
    emit_payment_confirmed(
        user_id=str(user_id),
        subscription_id=subscription_id,
        product_id=product_id,
    )


async def handle_subscription_updated(data, event_ts: datetime):
    """
    Handle any subscription field update.
    Primary sync mechanism for keeping state in sync.
    """
    subscription_id = data.subscription_id
    customer_id = data.customer.customer_id
    metadata = data.metadata or {}
    
    logger.info(f"Processing subscription.updated: {subscription_id}")
    
    # Find user by subscription, then customer_id, then metadata (for new users)
    user_id = await billing_service.find_user_by_subscription_id(subscription_id)
    if not user_id:
        user_id = await billing_service.find_user_by_customer_id(customer_id)
    if not user_id:
        user_id = await billing_service.find_user_by_metadata(metadata)
    
    if not user_id:
        logger.warning(f"Could not find user for subscription {subscription_id} in updated event")
        return
    
    # Sync all state
    await billing_service.apply_subscription_state(
        user_id=user_id,
        subscription_id=subscription_id,
        customer_id=customer_id,
        product_id=data.product_id,
        status=data.status,
        cancel_at_period_end=data.cancel_at_next_billing_date,
        current_period_start=data.previous_billing_date,
        current_period_end=data.next_billing_date,
        webhook_ts=event_ts,
    )


async def handle_subscription_renewed(data, event_ts: datetime):
    """
    Handle subscription renewal.
    Check for pending downgrades and apply them.
    """
    subscription_id = data.subscription_id
    customer_id = data.customer.customer_id
    metadata = data.metadata or {}
    
    logger.info(f"Processing subscription.renewed: {subscription_id}")
    
    # Find user by subscription, then customer_id, then metadata
    user_id = await billing_service.find_user_by_subscription_id(subscription_id)
    if not user_id:
        user_id = await billing_service.find_user_by_customer_id(customer_id)
    if not user_id:
        user_id = await billing_service.find_user_by_metadata(metadata)
    
    if user_id:
        await billing_service.apply_subscription_state(
            user_id=user_id,
            subscription_id=subscription_id,
            customer_id=customer_id,
            product_id=data.product_id,
            status="active",
            cancel_at_period_end=data.cancel_at_next_billing_date,
            current_period_start=data.previous_billing_date,
            current_period_end=data.next_billing_date,
            webhook_ts=event_ts,
        )


async def handle_subscription_plan_changed(data, event_ts: datetime):
    """
    Handle plan change (upgrade or applied downgrade).
    """
    subscription_id = data.subscription_id
    customer_id = data.customer.customer_id
    metadata = data.metadata or {}
    
    logger.info(f"Processing subscription.plan_changed: {subscription_id}")
    
    # Find user by subscription, then customer_id, then metadata
    user_id = await billing_service.find_user_by_subscription_id(subscription_id)
    if not user_id:
        user_id = await billing_service.find_user_by_customer_id(customer_id)
    if not user_id:
        user_id = await billing_service.find_user_by_metadata(metadata)
    
    if not user_id:
        logger.warning(f"Could not find user for subscription {subscription_id}")
        return
    
    await billing_service.apply_subscription_state(
        user_id=user_id,
        subscription_id=subscription_id,
        customer_id=customer_id,
        product_id=data.product_id,
        status=data.status,
        cancel_at_period_end=data.cancel_at_next_billing_date,
        current_period_start=data.previous_billing_date,
        current_period_end=data.next_billing_date,
        webhook_ts=event_ts,
    )


async def handle_subscription_cancelled(data, event_ts: datetime):
    """
    Handle subscription cancellation.
    User keeps access until period ends.
    """
    subscription_id = data.subscription_id
    customer_id = data.customer.customer_id
    metadata = data.metadata or {}
    
    logger.info(f"Processing subscription.cancelled: {subscription_id}")
    
    # Find user by subscription, then customer_id, then metadata
    user_id = await billing_service.find_user_by_subscription_id(subscription_id)
    if not user_id:
        user_id = await billing_service.find_user_by_customer_id(customer_id)
    if not user_id:
        user_id = await billing_service.find_user_by_metadata(metadata)
    
    if not user_id:
        logger.warning(f"Could not find user for subscription {subscription_id}")
        return
    
    await billing_service.apply_subscription_state(
        user_id=user_id,
        subscription_id=subscription_id,
        customer_id=customer_id,
        product_id=data.product_id,
        status="cancelled",
        cancel_at_period_end=True,
        current_period_start=data.previous_billing_date,
        current_period_end=data.next_billing_date,
        webhook_ts=event_ts,
    )


async def handle_subscription_expired(data, event_ts: datetime):
    """
    Handle subscription expiration.
    Access ends, revert user to free tier.
    """
    subscription_id = data.subscription_id
    customer_id = data.customer.customer_id
    metadata = data.metadata or {}
    
    logger.info(f"Processing subscription.expired: {subscription_id}")
    
    # Find user by subscription, then customer_id, then metadata
    user_id = await billing_service.find_user_by_subscription_id(subscription_id)
    if not user_id:
        user_id = await billing_service.find_user_by_customer_id(customer_id)
    if not user_id:
        user_id = await billing_service.find_user_by_metadata(metadata)
    
    if not user_id:
        logger.warning(f"Could not find user for subscription {subscription_id}")
        return
    
    await billing_service.apply_subscription_state(
        user_id=user_id,
        subscription_id=subscription_id,
        customer_id=customer_id,
        product_id=data.product_id,
        status="expired",
        cancel_at_period_end=data.cancel_at_next_billing_date,
        current_period_start=data.previous_billing_date,
        current_period_end=data.next_billing_date,
        webhook_ts=event_ts,
    )


async def handle_subscription_on_hold(data, event_ts: datetime):
    """
    Handle subscription put on hold (payment failed).
    """
    subscription_id = data.subscription_id
    customer_id = data.customer.customer_id
    metadata = data.metadata or {}
    
    logger.info(f"Processing subscription.on_hold: {subscription_id}")
    
    # Find user by subscription, then customer_id, then metadata
    user_id = await billing_service.find_user_by_subscription_id(subscription_id)
    if not user_id:
        user_id = await billing_service.find_user_by_customer_id(customer_id)
    if not user_id:
        user_id = await billing_service.find_user_by_metadata(metadata)
    
    if not user_id:
        logger.warning(f"Could not find user for subscription {subscription_id}")
        return
    
    await billing_service.apply_subscription_state(
        user_id=user_id,
        subscription_id=subscription_id,
        customer_id=customer_id,
        product_id=data.product_id,
        status="on_hold",
        cancel_at_period_end=data.cancel_at_next_billing_date,
        current_period_start=data.previous_billing_date,
        current_period_end=data.next_billing_date,
        webhook_ts=event_ts,
    )


async def handle_subscription_failed(data, event_ts: datetime):
    """Handle subscription creation or transition failure."""
    subscription_id = getattr(data, "subscription_id", None)
    customer = getattr(data, "customer", None)
    customer_id = getattr(customer, "customer_id", None)
    metadata = getattr(data, "metadata", None) or {}
    product_id = getattr(data, "product_id", None) or ""

    logger.info(f"Processing subscription.failed: {subscription_id}")

    user_id = None
    if subscription_id:
        user_id = await billing_service.find_user_by_subscription_id(subscription_id)
    if not user_id and customer_id:
        user_id = await billing_service.find_user_by_customer_id(customer_id)
    if not user_id:
        user_id = await billing_service.find_user_by_metadata(metadata)

    if not user_id or not subscription_id:
        logger.warning(f"Could not fully link failed subscription webhook: sub={subscription_id}, customer={customer_id}")
        return

    await billing_service.apply_subscription_state(
        user_id=user_id,
        subscription_id=subscription_id,
        customer_id=customer_id or "",
        product_id=product_id,
        status="failed",
        cancel_at_period_end=False,
        current_period_start=getattr(data, "previous_billing_date", None),
        current_period_end=getattr(data, "next_billing_date", None),
        webhook_ts=event_ts,
    )


async def handle_payment_succeeded(data) -> None:
    """Record successful payment lifecycle updates."""
    metadata = getattr(data, "metadata", None) or {}
    await billing_service.record_payment_event(
        payment_id=getattr(data, "payment_id", ""),
        subscription_id=getattr(data, "subscription_id", None),
        status="paid",
        amount=getattr(data, "total_amount", 0) or 0,
        currency=getattr(data, "currency", "USD") or "USD",
        metadata={
            **metadata,
            "payload_type": getattr(data, "payload_type", None),
        },
    )


async def handle_payment_failed(data) -> None:
    """Record failed payment lifecycle updates."""
    metadata = getattr(data, "metadata", None) or {}
    await billing_service.record_payment_event(
        payment_id=getattr(data, "payment_id", ""),
        subscription_id=getattr(data, "subscription_id", None),
        status="failed",
        amount=getattr(data, "total_amount", 0) or 0,
        currency=getattr(data, "currency", "USD") or "USD",
        failure_code=getattr(data, "failure_code", None),
        failure_message=getattr(data, "error_message", None) or getattr(data, "failure_message", None),
        metadata={
            **metadata,
            "payload_type": getattr(data, "payload_type", None),
        },
    )


async def handle_payment_processing(data) -> None:
    """Record processing payment lifecycle updates."""
    metadata = getattr(data, "metadata", None) or {}
    await billing_service.record_payment_event(
        payment_id=getattr(data, "payment_id", ""),
        subscription_id=getattr(data, "subscription_id", None),
        status="processing",
        amount=getattr(data, "total_amount", 0) or 0,
        currency=getattr(data, "currency", "USD") or "USD",
        metadata={
            **metadata,
            "payload_type": getattr(data, "payload_type", None),
        },
    )


async def handle_payment_cancelled(data) -> None:
    """Record cancelled payment lifecycle updates."""
    metadata = getattr(data, "metadata", None) or {}
    await billing_service.record_payment_event(
        payment_id=getattr(data, "payment_id", ""),
        subscription_id=getattr(data, "subscription_id", None),
        status="cancelled",
        amount=getattr(data, "total_amount", 0) or 0,
        currency=getattr(data, "currency", "USD") or "USD",
        metadata={
            **metadata,
            "payload_type": getattr(data, "payload_type", None),
        },
    )


def parse_datetime(value) -> datetime:
    """Parse datetime from various formats."""
    if value is None:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.utcnow()
