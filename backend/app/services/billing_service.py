"""Billing service for subscription management."""
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import text

from app.core import logger
from app.db.session import get_db_connection
from app.services import dodo_client

BILLING_ACTION_CHECKOUT = "checkout"
BILLING_ACTION_PREVIEW_CHANGE = "preview_change"
BILLING_ACTION_UPGRADE = "upgrade"
BILLING_ACTION_DOWNGRADE = "downgrade"
BILLING_ACTION_CANCEL = "cancel"
BILLING_ACTION_UNDO_CANCEL = "undo_cancel"
BILLING_ACTION_REACTIVATE = "reactivate"

STATE_TO_ALLOWED_ACTIONS = {
    "none": [BILLING_ACTION_CHECKOUT],
    "pending": [],
    "failed": [BILLING_ACTION_CHECKOUT],
    "expired": [BILLING_ACTION_CHECKOUT],
    "cancelled": [BILLING_ACTION_CHECKOUT],
    "on_hold": [BILLING_ACTION_REACTIVATE],
    "active": [
        BILLING_ACTION_PREVIEW_CHANGE,
        BILLING_ACTION_UPGRADE,
        BILLING_ACTION_DOWNGRADE,
        BILLING_ACTION_CANCEL,
    ],
    "active_cancel_scheduled": [
        BILLING_ACTION_PREVIEW_CHANGE,
        BILLING_ACTION_UPGRADE,
        BILLING_ACTION_DOWNGRADE,
        BILLING_ACTION_UNDO_CANCEL,
    ],
}


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from DB/webhook values."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _is_cancelled_with_access(subscription: Optional[dict]) -> bool:
    """True when cancelled subscription is still within paid access window."""
    if not subscription or subscription.get("status") != "cancelled":
        return False
    period_end = _parse_datetime(subscription.get("current_period_end"))
    return bool(period_end and period_end > datetime.now(timezone.utc))


def classify_billing_state(subscription: Optional[dict]) -> str:
    """Map subscription row to canonical billing state."""
    if not subscription:
        return "none"

    status = (subscription.get("status") or "").lower()
    cancel_at_period_end = bool(subscription.get("cancel_at_period_end"))

    if status == "active":
        return "active_cancel_scheduled" if cancel_at_period_end else "active"
    if status in STATE_TO_ALLOWED_ACTIONS:
        return status
    return "none"


def _pick_winner_subscription(subscriptions: list[dict]) -> Optional[dict]:
    """Pick effective subscription from per-subscription history."""
    if not subscriptions:
        return None

    now = datetime.now(timezone.utc)

    def _event_sort_key(sub: dict) -> tuple:
        period_end = _parse_datetime(sub.get("current_period_end")) or datetime.min.replace(tzinfo=timezone.utc)
        webhook_ts = _parse_datetime(sub.get("last_webhook_ts")) or datetime.min.replace(tzinfo=timezone.utc)
        return (period_end, webhook_ts)

    active = [s for s in subscriptions if (s.get("status") or "").lower() == "active"]
    if active:
        return max(active, key=_event_sort_key)

    on_hold = [s for s in subscriptions if (s.get("status") or "").lower() == "on_hold"]
    if on_hold:
        return max(on_hold, key=_event_sort_key)

    cancelled_with_access = []
    for sub in subscriptions:
        if (sub.get("status") or "").lower() != "cancelled":
            continue
        period_end = _parse_datetime(sub.get("current_period_end"))
        if period_end and period_end > now:
            cancelled_with_access.append(sub)
    if cancelled_with_access:
        return max(cancelled_with_access, key=_event_sort_key)

    return None


async def _get_user_role(user_id: UUID) -> str:
    """Read role directly from users table."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("SELECT role FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        )
        row = result.fetchone()
        return row[0] if row and row[0] else "free"


async def get_user_dodo_customer_id(user_id: UUID) -> Optional[str]:
    """Read persisted Dodo customer id for checkout/session reuse."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("SELECT dodo_customer_id FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        )
        row = result.fetchone()
        return row[0] if row and row[0] else None


async def get_billing_context(user_id: UUID) -> dict:
    """
    Return canonical billing state + allowed actions + subscription snapshot.
    """
    subscription = await get_user_subscription(user_id)
    state = classify_billing_state(subscription)
    allowed_actions = STATE_TO_ALLOWED_ACTIONS.get(state, [])
    cancelled_with_access = _is_cancelled_with_access(subscription)

    if subscription:
        db_role = subscription.get("db_role", "free")
    else:
        db_role = await _get_user_role(user_id)

    has_subscription = state in {"active", "active_cancel_scheduled", "on_hold", "cancelled"}
    access_granted = state in {"active", "active_cancel_scheduled", "on_hold"} or cancelled_with_access

    subscription_data = dict(subscription) if subscription else {}
    subscription_data.pop("db_role", None)

    return {
        "role": db_role,
        "billing_state": state,
        "allowed_actions": allowed_actions,
        "has_subscription": has_subscription,
        "access_granted": access_granted,
        "cancelled_with_access": cancelled_with_access,
        **subscription_data,
    }


def _blocked_action_error(action: str, state: str) -> str:
    """Consistent error message for action-gate violations."""
    if state == "on_hold":
        return "Your subscription is on hold due to a failed payment. Please update your payment method first."
    if state in {"failed", "expired", "cancelled"}:
        return "Please start a new subscription."
    if state == "pending":
        return "Your subscription is still pending. Please wait for activation."
    if state == "none":
        return "No active subscription found."
    if action == BILLING_ACTION_UNDO_CANCEL:
        return "Undo cancel is only available for active subscriptions scheduled for cancellation."
    if action == BILLING_ACTION_CANCEL:
        return "Cancel is only available for active subscriptions."
    return f"Cannot {action.replace('_', ' ')} while subscription is '{state}'."


async def require_allowed_action(user_id: UUID, action: str) -> dict:
    """Gate mutating billing actions through a single state contract."""
    context = await get_billing_context(user_id)
    if action not in context.get("allowed_actions", []):
        raise ValueError(_blocked_action_error(action, context["billing_state"]))
    return context


async def _sync_firebase_role(user_id: UUID, role: str) -> None:
    """Sync role to Firebase custom claims."""
    try:
        from firebase_admin import auth
        
        # Get firebase_uid from user_id
        async with get_db_connection() as conn:
            result = await conn.execute(
                text("SELECT firebase_uid FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
        
        if row and row[0]:
            firebase_uid = row[0]
            # Get existing claims and update role
            user = auth.get_user(firebase_uid)
            claims = user.custom_claims or {}
            claims["role"] = role
            auth.set_custom_user_claims(firebase_uid, claims)
            logger.info(f"Synced Firebase role for user {user_id}: role={role}")
    except Exception as e:
        logger.error(f"Failed to sync Firebase role for user {user_id}: {e}")


async def get_products() -> list[dict]:
    """Get all available subscription products."""
    return await dodo_client.get_products()


async def create_checkout(
    user_id: UUID,
    email: str,
    product_id: str,
    dodo_customer_id: Optional[str] = None,
) -> dict:
    """
    Create a checkout session for a product.
    Stores user_id in metadata for webhook linking.
    """
    session = await dodo_client.create_checkout_session(
        product_id=product_id,
        customer_id=dodo_customer_id,
        customer_email=email if not dodo_customer_id else None,
        metadata={"user_id": str(user_id)},
    )
    return session


async def get_user_subscription(user_id: UUID) -> Optional[dict]:
    """Get user's current effective subscription from subscription history."""
    async with get_db_connection() as conn:
        role_result = await conn.execute(
            text("SELECT role FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        )
        role_row = role_result.fetchone()
        db_role = role_row[0] if role_row and role_row[0] else "free"

        subscriptions: list[dict] = []
        result = await conn.execute(
            text("""
            SELECT
                subscription_id, customer_id, product_id, status,
                cancel_at_period_end, current_period_start, current_period_end, last_webhook_ts
            FROM billing_subscriptions
            WHERE user_id = :user_id
            ORDER BY last_webhook_ts DESC
            """),
            {"user_id": user_id},
        )
        for row in result.fetchall():
            subscriptions.append(
                {
                    "subscription_id": row[0],
                    "customer_id": row[1],
                    "product_id": row[2],
                    "status": row[3],
                    "cancel_at_period_end": row[4],
                    "current_period_start": row[5].isoformat() if row[5] else None,
                    "current_period_end": row[6].isoformat() if row[6] else None,
                    "last_webhook_ts": row[7].isoformat() if row[7] else None,
                }
            )

        subscription = _pick_winner_subscription(subscriptions)
        if not subscription:
            return None
        subscription["db_role"] = db_role

        # Check for pending plan change
        pending_result = await conn.execute(
            text("""
            SELECT target_product_id, target_role, created_at
            FROM pending_plan_changes
            WHERE user_id = :user_id
              AND subscription_id = :subscription_id
              AND status = 'pending'
            ORDER BY created_at DESC LIMIT 1
            """),
            {
                "user_id": user_id,
                "subscription_id": subscription["subscription_id"],
            }
        )
        pending_row = pending_result.fetchone()
        
        if pending_row:
            subscription["pending_downgrade"] = {
                "target_product_id": pending_row[0],
                "target_role": pending_row[1],
                "created_at": pending_row[2].isoformat(),
            }
        
        return subscription


async def request_upgrade(
    user_id: UUID,
    target_product_id: str,
) -> dict:
    """
    Request an immediate upgrade.
    Calls Dodo changePlan with prorated_immediately.
    """
    context = await require_allowed_action(user_id, BILLING_ACTION_UPGRADE)
    subscription_id = context.get("subscription_id")
    current_product_id = context.get("product_id")
    if not subscription_id or not current_product_id:
        raise ValueError("No active subscription found")
    
    # Verify target is actually an upgrade (higher credits)
    products = await dodo_client.get_products()
    current_product = next((p for p in products if p["product_id"] == current_product_id), None)
    target_product = next((p for p in products if p["product_id"] == target_product_id), None)
    
    if not target_product:
        raise ValueError(f"Product {target_product_id} not found")    
    
    current_credits = int(current_product["metadata"].get("credits", 0)) if current_product else 0
    target_credits = int(target_product["metadata"].get("credits", 0))
    current_price = current_product.get("price", 0) if current_product else 0
    target_price = target_product.get("price", 0)
    
    logger.info(f"Upgrade check: current_credits={current_credits}, target_credits={target_credits}, current_price={current_price}, target_price={target_price}")
    
    # Allow upgrade if:
    # 1. More credits (higher tier)
    # 2. Same credits but higher price (Monthly -> Yearly upsell)
    is_upgrade = target_credits > current_credits or (target_credits == current_credits and target_price > current_price)
    
    if not is_upgrade:
        raise ValueError("Target plan must be an upgrade (more credits or higher price). Use downgrade endpoint for lower tiers.")
    
    # Cancel any pending downgrade
    await cancel_pending_downgrade(user_id)
    
    # Call Dodo to change plan immediately
    result = await dodo_client.change_plan(
        subscription_id=subscription_id,
        product_id=target_product_id,
        proration_mode="prorated_immediately",
    )
    
    logger.info(f"Upgrade initiated for user {user_id}: {current_product_id} -> {target_product_id}")
    return result


async def request_downgrade(
    user_id: UUID,
    target_product_id: str,
) -> dict:
    """
    Request a downgrade at end of billing cycle.
    Stores in pending_plan_changes, applied on subscription.renewed webhook.
    """
    context = await require_allowed_action(user_id, BILLING_ACTION_DOWNGRADE)
    subscription_id = context.get("subscription_id")
    current_product_id = context.get("product_id")
    if not subscription_id or not current_product_id:
        raise ValueError("No active subscription found")
    
    # Verify target is actually a downgrade (lower credits)
    products = await dodo_client.get_products()
    current_product = next((p for p in products if p["product_id"] == current_product_id), None)
    target_product = next((p for p in products if p["product_id"] == target_product_id), None)
    
    if not target_product:
        raise ValueError(f"Product {target_product_id} not found")
    
    current_credits = int(current_product["metadata"].get("credits", 0)) if current_product else 0
    target_credits = int(target_product["metadata"].get("credits", 0))
    current_price = current_product.get("price", 0) if current_product else 0
    target_price = target_product.get("price", 0)
    target_role = target_product["metadata"].get("app_role", "free")
    
    # Allow downgrade if:
    # 1. Fewer credits (lower tier)
    # 2. Same credits but lower price (Yearly -> Monthly downsell)
    is_downgrade = target_credits < current_credits or (target_credits == current_credits and target_price < current_price)
    
    if not is_downgrade:
        raise ValueError("Target plan must be a downgrade (fewer credits or lower price). Use upgrade endpoint instead.")
    
    # Cancel any existing pending downgrade
    await cancel_pending_downgrade(user_id)
    
    # Store pending downgrade
    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            INSERT INTO pending_plan_changes 
                (user_id, subscription_id, target_product_id, target_role, status)
            VALUES 
                (:user_id, :subscription_id, :target_product_id, :target_role, 'pending')
            """),
            {
                "user_id": user_id,
                "subscription_id": subscription_id,
                "target_product_id": target_product_id,
                "target_role": target_role,
            }
        )
    
    logger.info(f"Downgrade scheduled for user {user_id}: {current_product_id} -> {target_product_id} at end of cycle")
    
    return {
        "message": "Downgrade scheduled for end of billing cycle",
        "effective_at": context.get("current_period_end"),
        "target_product_id": target_product_id,
        "target_role": target_role,
    }


async def cancel_pending_downgrade(user_id: UUID) -> bool:
    """Cancel any pending downgrade for user."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            UPDATE pending_plan_changes
            SET status = 'cancelled', cancelled_at = now()
            WHERE user_id = :user_id AND status = 'pending'
            """),
            {"user_id": user_id}
        )
        cancelled = result.rowcount > 0
        if cancelled:
            logger.info(f"Cancelled pending downgrade for user {user_id}")
        return cancelled


async def request_cancel(user_id: UUID) -> dict:
    """
    Request subscription cancellation at end of billing period.
    User keeps access until period ends.
    """
    context = await require_allowed_action(user_id, BILLING_ACTION_CANCEL)
    subscription_id = context.get("subscription_id")
    if not subscription_id:
        raise ValueError("No active subscription found")
    
    # Cancel any pending downgrade since subscription will end
    await cancel_pending_downgrade(user_id)
    
    # Set cancel_at_period_end via Dodo
    await dodo_client.set_cancel_at_period_end(
        subscription_id=subscription_id,
        cancel=True,
    )
    
    logger.info(f"Cancellation scheduled for user {user_id} at end of period")
    
    return {
        "message": "Subscription will cancel at end of billing period",
        "access_until": context.get("current_period_end"),
    }


async def undo_cancel(user_id: UUID) -> dict:
    """Undo scheduled cancellation."""
    context = await require_allowed_action(user_id, BILLING_ACTION_UNDO_CANCEL)
    subscription_id = context.get("subscription_id")
    if not subscription_id:
        raise ValueError("No active subscription found")
    
    await dodo_client.set_cancel_at_period_end(
        subscription_id=subscription_id,
        cancel=False,
    )
    
    logger.info(f"Cancellation undone for user {user_id}")
    
    return {"message": "Subscription cancellation has been undone"}


async def apply_subscription_state(
    user_id: UUID,
    subscription_id: str,
    customer_id: str,
    product_id: str,
    status: str,
    cancel_at_period_end: bool,
    current_period_start: datetime,
    current_period_end: datetime,
    webhook_ts: datetime,
    is_new_subscription: bool = False,
    is_plan_change: bool = False,
) -> None:
    """
    Apply subscription state from webhook.
    Updates canonical subscription history and recomputes winner-derived user state.
    
    is_new_subscription: Set credit_period_start (first subscription)
    is_plan_change: Retained for compatibility (credits no longer reset on plan change)
    """
    async with get_db_connection() as conn:
        existing_owner_result = await conn.execute(
            text("""
            SELECT user_id
            FROM billing_subscriptions
            WHERE subscription_id = :subscription_id
            """),
            {"subscription_id": subscription_id},
        )
        existing_owner_row = existing_owner_result.fetchone()
        if existing_owner_row and existing_owner_row[0] != user_id:
            logger.warning(
                "Subscription owner mismatch for %s: incoming_user=%s existing_user=%s. Keeping existing owner.",
                subscription_id,
                user_id,
                existing_owner_row[0],
            )
            user_id = existing_owner_row[0]

        # Canonical per-subscription history table (new model).
        await conn.execute(
            text("""
            INSERT INTO billing_subscriptions
                (user_id, subscription_id, customer_id, product_id, status,
                 cancel_at_period_end, current_period_start, current_period_end,
                 last_webhook_ts, updated_at)
            VALUES
                (:user_id, :subscription_id, :customer_id, :product_id, :status,
                 :cancel_at_period_end, :current_period_start, :current_period_end,
                 :webhook_ts, now())
            ON CONFLICT (subscription_id) DO UPDATE SET
                -- Keep subscription owner immutable once first linked.
                user_id = billing_subscriptions.user_id,
                customer_id = EXCLUDED.customer_id,
                product_id = EXCLUDED.product_id,
                status = EXCLUDED.status,
                cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                current_period_start = EXCLUDED.current_period_start,
                current_period_end = EXCLUDED.current_period_end,
                last_webhook_ts = EXCLUDED.last_webhook_ts,
                updated_at = now()
            WHERE billing_subscriptions.last_webhook_ts < EXCLUDED.last_webhook_ts
            """),
            {
                "user_id": user_id,
                "subscription_id": subscription_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "status": status,
                "cancel_at_period_end": cancel_at_period_end,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
                "webhook_ts": webhook_ts,
            },
        )

        # Recompute winner from all subscriptions for this user.
        winner_result = await conn.execute(
            text("""
            SELECT
                subscription_id, customer_id, product_id, status,
                cancel_at_period_end, current_period_start, current_period_end, last_webhook_ts
            FROM billing_subscriptions
            WHERE user_id = :user_id
            ORDER BY last_webhook_ts DESC
            """),
            {"user_id": user_id},
        )
        candidates = []
        for row in winner_result.fetchall():
            candidates.append(
                {
                    "subscription_id": row[0],
                    "customer_id": row[1],
                    "product_id": row[2],
                    "status": row[3],
                    "cancel_at_period_end": row[4],
                    "current_period_start": row[5].isoformat() if row[5] else None,
                    "current_period_end": row[6].isoformat() if row[6] else None,
                    "last_webhook_ts": row[7].isoformat() if row[7] else None,
                }
            )
        winner = _pick_winner_subscription(candidates)

        new_role = "free"
        period_start_to_set = datetime.now(timezone.utc)
        customer_id_to_set = customer_id

        if winner:
            winner_product = dodo_client.get_product_by_id(winner["product_id"])
            if not winner_product:
                await dodo_client.get_products()
                winner_product = dodo_client.get_product_by_id(winner["product_id"])
            new_role = winner_product["metadata"].get("app_role", "free") if winner_product else "free"
            period_start_to_set = _parse_datetime(winner.get("current_period_start")) or datetime.now(timezone.utc)
            customer_id_to_set = winner.get("customer_id") or customer_id

        reset_credit_period = (
            is_new_subscription
            and winner
            and winner.get("subscription_id") == subscription_id
            and (winner.get("status") or "").lower() == "active"
        )

        if reset_credit_period:
            await conn.execute(
                text("""
                UPDATE users
                SET role = :role,
                    current_period_start = :period_start,
                    credit_period_start = now(),
                    dodo_customer_id = :customer_id
                WHERE id = :user_id
                """),
                {
                    "user_id": user_id,
                    "role": new_role,
                    "period_start": period_start_to_set,
                    "customer_id": customer_id_to_set,
                },
            )
        else:
            await conn.execute(
                text("""
                UPDATE users
                SET role = :role,
                    current_period_start = :period_start,
                    dodo_customer_id = :customer_id
                WHERE id = :user_id
                """),
                {
                    "user_id": user_id,
                    "role": new_role,
                    "period_start": period_start_to_set,
                    "customer_id": customer_id_to_set,
                },
            )

    await _sync_firebase_role(user_id, new_role)
    logger.info(
        f"Applied subscription state for user {user_id}: incoming_status={status}, winner={winner.get('subscription_id') if winner else 'none'}, role={new_role}"
    )


async def revert_to_free(user_id: UUID) -> None:
    """Revert user to free tier (subscription expired)."""
    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            UPDATE users
            SET role = 'free',
                current_period_start = now()
            WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        
        # Update subscription statuses
        await conn.execute(
            text("""
            UPDATE billing_subscriptions
            SET status = 'expired', updated_at = now()
            WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        )
    
    logger.info(f"Reverted user {user_id} to free tier")
    
    # Sync role to Firebase
    await _sync_firebase_role(user_id, "free")


async def get_pending_downgrade(subscription_id: str) -> Optional[dict]:
    """Get pending downgrade for a subscription."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            SELECT id, user_id, target_product_id, target_role
            FROM pending_plan_changes
            WHERE subscription_id = :subscription_id AND status = 'pending'
            ORDER BY created_at DESC LIMIT 1
            """),
            {"subscription_id": subscription_id}
        )
        row = result.fetchone()
        
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "target_product_id": row[2],
                "target_role": row[3],
            }
        return None


async def mark_pending_applied(pending_id: UUID) -> None:
    """Mark a pending plan change as applied."""
    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            UPDATE pending_plan_changes
            SET status = 'applied', applied_at = now()
            WHERE id = :id
            """),
            {"id": pending_id}
        )
    logger.info(f"Marked pending plan change {pending_id} as applied")


async def recompute_user_billing_winner(user_id: UUID) -> dict:
    """
    Recompute effective subscription winner for a user from billing_subscriptions.
    Useful after backfills/replays.
    """
    winner: Optional[dict] = None
    new_role = "free"
    period_start_to_set = datetime.now(timezone.utc)
    customer_id_to_set: Optional[str] = None

    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            SELECT
                subscription_id, customer_id, product_id, status,
                cancel_at_period_end, current_period_start, current_period_end, last_webhook_ts
            FROM billing_subscriptions
            WHERE user_id = :user_id
            ORDER BY last_webhook_ts DESC
            """),
            {"user_id": user_id},
        )
        subscriptions = []
        for row in result.fetchall():
            subscriptions.append(
                {
                    "subscription_id": row[0],
                    "customer_id": row[1],
                    "product_id": row[2],
                    "status": row[3],
                    "cancel_at_period_end": row[4],
                    "current_period_start": row[5].isoformat() if row[5] else None,
                    "current_period_end": row[6].isoformat() if row[6] else None,
                    "last_webhook_ts": row[7].isoformat() if row[7] else None,
                }
            )
        winner = _pick_winner_subscription(subscriptions)
        if winner:
            winner_product = dodo_client.get_product_by_id(winner["product_id"])
            if not winner_product:
                await dodo_client.get_products()
                winner_product = dodo_client.get_product_by_id(winner["product_id"])
            new_role = winner_product["metadata"].get("app_role", "free") if winner_product else "free"
            period_start_to_set = _parse_datetime(winner.get("current_period_start")) or datetime.now(timezone.utc)
            customer_id_to_set = winner.get("customer_id")

        await conn.execute(
            text("""
            UPDATE users
            SET role = :role,
                current_period_start = :period_start,
                dodo_customer_id = COALESCE(:customer_id, dodo_customer_id)
            WHERE id = :user_id
            """),
            {
                "user_id": user_id,
                "role": new_role,
                "period_start": period_start_to_set,
                "customer_id": customer_id_to_set,
            },
        )

    await _sync_firebase_role(user_id, new_role)
    return {
        "user_id": str(user_id),
        "winner_subscription_id": winner.get("subscription_id") if winner else None,
        "role": new_role,
    }


async def find_user_by_metadata(metadata: dict) -> Optional[UUID]:
    """Find user ID from checkout metadata."""
    user_id_str = metadata.get("user_id")
    if user_id_str:
        try:
            return UUID(user_id_str)
        except (ValueError, TypeError):
            pass
    return None


async def find_user_by_customer_id(customer_id: str) -> Optional[UUID]:
    """Find user ID from Dodo customer ID."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("SELECT id FROM users WHERE dodo_customer_id = :customer_id"),
            {"customer_id": customer_id}
        )
        row = result.fetchone()
        return row[0] if row else None


async def find_user_by_subscription_id(subscription_id: str) -> Optional[UUID]:
    """Find user ID from subscription ID."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("SELECT user_id FROM billing_subscriptions WHERE subscription_id = :subscription_id"),
            {"subscription_id": subscription_id},
        )
        row = result.fetchone()
        return row[0] if row else None
