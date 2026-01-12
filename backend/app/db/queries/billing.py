"""Billing-related database queries.

Handles:
- Webhook event deduplication
- User subscription state (normalized)
- Pending plan changes (scheduled downgrades)
- Product cache
"""
import json
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import logger


def now_utc() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


# ============================================================================
# WEBHOOK EVENTS
# ============================================================================

async def upsert_webhook_event(
    conn: AsyncConnection,
    *,
    webhook_id: str,
    event_type: str,
    event_ts: datetime,
    subscription_id: str | None,
    payload: dict,
) -> bool:
    """
    Insert webhook event for deduplication.
    Returns True if inserted (first time), False if already exists.
    """
    result = await conn.execute(
        text("""
            INSERT INTO webhook_events (webhook_id, event_type, event_ts, subscription_id, payload, received_at)
            VALUES (:wid, :etype, :ets, :sid, CAST(:payload AS jsonb), :received_at)
            ON CONFLICT (webhook_id) DO NOTHING
            RETURNING webhook_id
        """),
        {
            "wid": webhook_id,
            "etype": event_type,
            "ets": event_ts,
            "sid": subscription_id,
            "payload": json.dumps(payload),
            "received_at": now_utc(),
        },
    )
    return result.fetchone() is not None


async def mark_webhook_processed(
    conn: AsyncConnection,
    webhook_id: str,
    status: str = "ok",
    error: str | None = None,
) -> None:
    """Mark webhook as processed with status."""
    await conn.execute(
        text("""
            UPDATE webhook_events
            SET processed_at = :processed_at, process_status = :status, error = :error
            WHERE webhook_id = :wid
        """),
        {
            "processed_at": now_utc(),
            "status": status,
            "error": error[:5000] if error else None,
            "wid": webhook_id,
        },
    )


# ============================================================================
# USER SUBSCRIPTIONS
# ============================================================================

async def get_user_subscription(
    conn: AsyncConnection,
    user_id: UUID,
) -> dict | None:
    """Get user's current subscription state."""
    result = await conn.execute(
        text("""
            SELECT 
                id, user_id, subscription_id, customer_id, product_id,
                status, cancel_at_next_billing_date, cancelled_at,
                current_period_start, current_period_end, expires_at,
                last_event_ts, created_at, updated_at
            FROM user_subscriptions
            WHERE user_id = :user_id
            ORDER BY updated_at DESC
            LIMIT 1
        """),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        return None
    
    return {
        "id": row[0],
        "user_id": row[1],
        "subscription_id": row[2],
        "customer_id": row[3],
        "product_id": row[4],
        "status": row[5],
        "cancel_at_next_billing_date": row[6],
        "cancelled_at": row[7],
        "current_period_start": row[8],
        "current_period_end": row[9],
        "expires_at": row[10],
        "last_event_ts": row[11],
        "created_at": row[12],
        "updated_at": row[13],
    }


async def get_subscription_by_id(
    conn: AsyncConnection,
    subscription_id: str,
) -> dict | None:
    """Get subscription by Dodo subscription ID."""
    result = await conn.execute(
        text("""
            SELECT 
                id, user_id, subscription_id, customer_id, product_id,
                status, cancel_at_next_billing_date, cancelled_at,
                current_period_start, current_period_end, expires_at,
                last_event_ts, created_at, updated_at
            FROM user_subscriptions
            WHERE subscription_id = :sid
            LIMIT 1
        """),
        {"sid": subscription_id},
    )
    row = result.fetchone()
    if not row:
        return None
    
    return {
        "id": row[0],
        "user_id": row[1],
        "subscription_id": row[2],
        "customer_id": row[3],
        "product_id": row[4],
        "status": row[5],
        "cancel_at_next_billing_date": row[6],
        "cancelled_at": row[7],
        "current_period_start": row[8],
        "current_period_end": row[9],
        "expires_at": row[10],
        "last_event_ts": row[11],
        "created_at": row[12],
        "updated_at": row[13],
    }


async def get_last_event_ts(
    conn: AsyncConnection,
    subscription_id: str,
) -> datetime | None:
    """Get last event timestamp for out-of-order protection."""
    result = await conn.execute(
        text("SELECT last_event_ts FROM user_subscriptions WHERE subscription_id = :sid"),
        {"sid": subscription_id},
    )
    row = result.fetchone()
    return row[0] if row else None


async def upsert_user_subscription(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    subscription_id: str,
    customer_id: str | None,
    product_id: str,
    status: str,
    cancel_at_next_billing_date: bool,
    cancelled_at: datetime | None,
    current_period_start: datetime | None,
    current_period_end: datetime | None,
    expires_at: datetime | None,
    event_ts: datetime,
) -> None:
    """Upsert subscription from webhook snapshot."""
    await conn.execute(
        text("""
            INSERT INTO user_subscriptions (
                user_id, subscription_id, customer_id, product_id, status,
                cancel_at_next_billing_date, cancelled_at,
                current_period_start, current_period_end, expires_at,
                last_event_ts, updated_at
            )
            VALUES (
                :user_id, :sid, :cid, :pid, :status,
                :cancel_at, :cancelled_at,
                :cps, :cpe, :expires_at,
                :event_ts, :updated_at
            )
            ON CONFLICT (subscription_id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                customer_id = COALESCE(EXCLUDED.customer_id, user_subscriptions.customer_id),
                product_id = EXCLUDED.product_id,
                status = EXCLUDED.status,
                cancel_at_next_billing_date = EXCLUDED.cancel_at_next_billing_date,
                cancelled_at = EXCLUDED.cancelled_at,
                current_period_start = EXCLUDED.current_period_start,
                current_period_end = EXCLUDED.current_period_end,
                expires_at = EXCLUDED.expires_at,
                last_event_ts = EXCLUDED.last_event_ts,
                updated_at = EXCLUDED.updated_at
        """),
        {
            "user_id": user_id,
            "sid": subscription_id,
            "cid": customer_id,
            "pid": product_id,
            "status": status,
            "cancel_at": cancel_at_next_billing_date,
            "cancelled_at": cancelled_at,
            "cps": current_period_start,
            "cpe": current_period_end,
            "expires_at": expires_at,
            "event_ts": event_ts,
            "updated_at": now_utc(),
        },
    )
    await conn.commit()


# ============================================================================
# PENDING PLAN CHANGES (Scheduled Downgrades)
# ============================================================================

async def create_pending_plan_change(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    subscription_id: str,
    current_product_id: str,
    target_product_id: str,
    target_role: str,
    effective_at: datetime,
) -> UUID:
    """Create a pending plan change (scheduled downgrade)."""
    # Cancel any existing pending changes for this user first
    await cancel_pending_plan_changes(conn, user_id)
    
    result = await conn.execute(
        text("""
            INSERT INTO pending_plan_changes (
                user_id, subscription_id, current_product_id, 
                target_product_id, target_role, effective_at, status
            )
            VALUES (:user_id, :sid, :current_pid, :target_pid, :target_role, :effective_at, 'pending')
            RETURNING id
        """),
        {
            "user_id": user_id,
            "sid": subscription_id,
            "current_pid": current_product_id,
            "target_pid": target_product_id,
            "target_role": target_role,
            "effective_at": effective_at,
        },
    )
    await conn.commit()
    return result.fetchone()[0]


async def get_pending_plan_change(
    conn: AsyncConnection,
    user_id: UUID,
) -> dict | None:
    """Get pending plan change for user."""
    result = await conn.execute(
        text("""
            SELECT id, subscription_id, current_product_id, target_product_id, 
                   target_role, effective_at, status, created_at
            FROM pending_plan_changes
            WHERE user_id = :user_id AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        return None
    
    return {
        "id": row[0],
        "subscription_id": row[1],
        "current_product_id": row[2],
        "target_product_id": row[3],
        "target_role": row[4],
        "effective_at": row[5],
        "status": row[6],
        "created_at": row[7],
    }


async def get_pending_changes_to_apply(
    conn: AsyncConnection,
    subscription_id: str,
) -> dict | None:
    """Get pending change for a subscription that should be applied."""
    result = await conn.execute(
        text("""
            SELECT id, user_id, subscription_id, current_product_id, target_product_id, 
                   target_role, effective_at, status, created_at
            FROM pending_plan_changes
            WHERE subscription_id = :sid AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"sid": subscription_id},
    )
    row = result.fetchone()
    if not row:
        return None
    
    return {
        "id": row[0],
        "user_id": row[1],
        "subscription_id": row[2],
        "current_product_id": row[3],
        "target_product_id": row[4],
        "target_role": row[5],
        "effective_at": row[6],
        "status": row[7],
        "created_at": row[8],
    }


async def mark_pending_change_applied(
    conn: AsyncConnection,
    change_id: UUID,
) -> None:
    """Mark pending plan change as applied."""
    await conn.execute(
        text("""
            UPDATE pending_plan_changes
            SET status = 'applied', applied_at = :applied_at
            WHERE id = :id
        """),
        {"id": change_id, "applied_at": now_utc()},
    )
    await conn.commit()


async def cancel_pending_plan_changes(
    conn: AsyncConnection,
    user_id: UUID,
) -> int:
    """Cancel all pending plan changes for user. Returns count cancelled."""
    result = await conn.execute(
        text("""
            UPDATE pending_plan_changes
            SET status = 'cancelled', cancelled_at = :cancelled_at
            WHERE user_id = :user_id AND status = 'pending'
        """),
        {"user_id": user_id, "cancelled_at": now_utc()},
    )
    await conn.commit()
    return result.rowcount


# ============================================================================
# PRODUCT CACHE
# ============================================================================

async def get_product(
    conn: AsyncConnection,
    product_id: str,
) -> dict | None:
    """Get cached product by ID."""
    result = await conn.execute(
        text("""
            SELECT product_id, name, is_recurring, price, currency, metadata, updated_at
            FROM dodo_products
            WHERE product_id = :pid
        """),
        {"pid": product_id},
    )
    row = result.fetchone()
    if not row:
        return None
    
    return {
        "product_id": row[0],
        "name": row[1],
        "is_recurring": row[2],
        "price": row[3],
        "currency": row[4],
        "metadata": row[5] or {},
        "updated_at": row[6],
    }


async def get_role_for_product(
    conn: AsyncConnection,
    product_id: str,
) -> str | None:
    """Get app role from product metadata."""
    result = await conn.execute(
        text("SELECT metadata FROM dodo_products WHERE product_id = :pid"),
        {"pid": product_id},
    )
    row = result.fetchone()
    if not row:
        return None
    
    metadata = row[0] or {}
    app_role = metadata.get("app_role")
    
    # Validate it's a known role
    if app_role in {"free", "creator", "pro_research"}:
        return app_role
    return None


async def upsert_product(
    conn: AsyncConnection,
    *,
    product_id: str,
    name: str,
    is_recurring: bool,
    price: int | None,
    currency: str | None,
    metadata: dict,
    raw: dict | None = None,
) -> None:
    """Upsert product into cache."""
    await conn.execute(
        text("""
            INSERT INTO dodo_products (product_id, name, is_recurring, price, currency, metadata, updated_at, raw)
            VALUES (:pid, :name, :is_recurring, :price, :currency, CAST(:metadata AS jsonb), :updated_at, CAST(:raw AS jsonb))
            ON CONFLICT (product_id) DO UPDATE SET
                name = EXCLUDED.name,
                is_recurring = EXCLUDED.is_recurring,
                price = EXCLUDED.price,
                currency = EXCLUDED.currency,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at,
                raw = EXCLUDED.raw
        """),
        {
            "pid": product_id,
            "name": name,
            "is_recurring": is_recurring,
            "price": price,
            "currency": currency,
            "metadata": json.dumps(metadata),
            "updated_at": now_utc(),
            "raw": json.dumps(raw) if raw else None,
        },
    )
    await conn.commit()


async def product_exists(
    conn: AsyncConnection,
    product_id: str,
) -> bool:
    """Check if product exists in cache."""
    result = await conn.execute(
        text("SELECT 1 FROM dodo_products WHERE product_id = :pid LIMIT 1"),
        {"pid": product_id},
    )
    return result.fetchone() is not None


# ============================================================================
# USER RESOLUTION HELPERS
# ============================================================================

async def get_user_id_by_subscription(
    conn: AsyncConnection,
    subscription_id: str,
) -> UUID | None:
    """Get user ID from subscription ID (fallback lookup)."""
    result = await conn.execute(
        text("SELECT user_id FROM user_subscriptions WHERE subscription_id = :sid LIMIT 1"),
        {"sid": subscription_id},
    )
    row = result.fetchone()
    return row[0] if row else None


async def get_user_id_by_customer(
    conn: AsyncConnection,
    customer_id: str,
) -> UUID | None:
    """Get user ID from Dodo customer ID (fallback lookup)."""
    result = await conn.execute(
        text("SELECT id FROM users WHERE dodo_customer_id = :cid LIMIT 1"),
        {"cid": customer_id},
    )
    row = result.fetchone()
    return row[0] if row else None
