"""Billing service for subscription management."""
import json
from uuid import UUID
from datetime import datetime
from typing import Optional

from sqlalchemy import text

from app.core import logger
from app.db.session import get_db_connection
from app.services import dodo_client


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
    """Get user's current subscription and any pending plan change."""
    async with get_db_connection() as conn:
        # Get subscription AND user's current role from DB
        result = await conn.execute(
            text("""
            SELECT 
                us.subscription_id, us.customer_id, us.product_id, us.status,
                us.cancel_at_period_end, us.current_period_start, us.current_period_end,
                u.role
            FROM user_subscriptions us
            JOIN users u ON u.id = us.user_id
            WHERE us.user_id = :user_id
            """),
            {"user_id": user_id}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        subscription = {
            "subscription_id": row[0],
            "customer_id": row[1],
            "product_id": row[2],
            "status": row[3],
            "cancel_at_period_end": row[4],
            "current_period_start": row[5].isoformat() if row[5] else None,
            "current_period_end": row[6].isoformat() if row[6] else None,
            "db_role": row[7],  # User's actual role from DB
        }
        
        # Check for pending plan change
        pending_result = await conn.execute(
            text("""
            SELECT target_product_id, target_role, created_at
            FROM pending_plan_changes
            WHERE user_id = :user_id AND status = 'pending'
            ORDER BY created_at DESC LIMIT 1
            """),
            {"user_id": user_id}
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
    subscription = await get_user_subscription(user_id)
    if not subscription:
        raise ValueError("No active subscription found")
    
    # Guard: only allow plan changes on active subscriptions
    sub_status = subscription.get("status")
    if sub_status != "active":
        if sub_status == "on_hold":
            raise ValueError("Your subscription is on hold due to a failed payment. Please update your payment method first.")
        elif sub_status == "failed":
            raise ValueError("Your previous subscription attempt failed. Please start a new subscription.")
        else:
            raise ValueError(f"Cannot change plan: subscription is '{sub_status}'.")
    
    # Verify target is actually an upgrade (higher credits)
    products = await dodo_client.get_products()
    current_product = next((p for p in products if p["product_id"] == subscription["product_id"]), None)
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
        subscription_id=subscription["subscription_id"],
        product_id=target_product_id,
        proration_mode="prorated_immediately",
    )
    
    logger.info(f"Upgrade initiated for user {user_id}: {subscription['product_id']} -> {target_product_id}")
    return result


async def request_downgrade(
    user_id: UUID,
    target_product_id: str,
) -> dict:
    """
    Request a downgrade at end of billing cycle.
    Stores in pending_plan_changes, applied on subscription.renewed webhook.
    """
    subscription = await get_user_subscription(user_id)
    if not subscription:
        raise ValueError("No active subscription found")
    
    # Guard: only allow plan changes on active subscriptions
    sub_status = subscription.get("status")
    if sub_status != "active":
        if sub_status == "on_hold":
            raise ValueError("Your subscription is on hold due to a failed payment. Please update your payment method first.")
        elif sub_status == "failed":
            raise ValueError("Your previous subscription attempt failed. Please start a new subscription.")
        else:
            raise ValueError(f"Cannot change plan: subscription is '{sub_status}'.")
    
    # Verify target is actually a downgrade (lower credits)
    products = await dodo_client.get_products()
    current_product = next((p for p in products if p["product_id"] == subscription["product_id"]), None)
    target_product = next((p for p in products if p["product_id"] == target_product_id), None)
    
    if not target_product:
        raise ValueError(f"Product {target_product_id} not found")
    
    current_credits = int(current_product["metadata"].get("credits", 0)) if current_product else 0
    target_credits = int(target_product["metadata"].get("credits", 0))
    current_price = getattr(current_product, "price", 0) if isinstance(current_product, object) else current_product.get("price", 0)
    target_price = getattr(target_product, "price", 0) if isinstance(target_product, object) else target_product.get("price", 0)
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
                "subscription_id": subscription["subscription_id"],
                "target_product_id": target_product_id,
                "target_role": target_role,
            }
        )
    
    logger.info(f"Downgrade scheduled for user {user_id}: {subscription['product_id']} -> {target_product_id} at end of cycle")
    
    return {
        "message": "Downgrade scheduled for end of billing cycle",
        "effective_at": subscription["current_period_end"],
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
    subscription = await get_user_subscription(user_id)
    if not subscription:
        raise ValueError("No active subscription found")
    
    # Cancel any pending downgrade since subscription will end
    await cancel_pending_downgrade(user_id)
    
    # Set cancel_at_period_end via Dodo
    await dodo_client.set_cancel_at_period_end(
        subscription_id=subscription["subscription_id"],
        cancel=True,
    )
    
    logger.info(f"Cancellation scheduled for user {user_id} at end of period")
    
    return {
        "message": "Subscription will cancel at end of billing period",
        "access_until": subscription["current_period_end"],
    }


async def undo_cancel(user_id: UUID) -> dict:
    """Undo scheduled cancellation."""
    subscription = await get_user_subscription(user_id)
    if not subscription:
        raise ValueError("No active subscription found")
    
    await dodo_client.set_cancel_at_period_end(
        subscription_id=subscription["subscription_id"],
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
    Updates user_subscriptions table and user role/period_start.
    
    is_new_subscription: Set credit_period_start (first subscription)
    is_plan_change: Reset credit_period_start (upgrade/downgrade)
    """
    # Get product metadata for role
    product = dodo_client.get_product_by_id(product_id)
    if not product:
        # Refresh cache and try again
        await dodo_client.get_products()
        product = dodo_client.get_product_by_id(product_id)
    
    role = product["metadata"].get("app_role", "free") if product else "free"
    
    async with get_db_connection() as conn:
        # Upsert subscription (with out-of-order protection)
        await conn.execute(
            text("""
            INSERT INTO user_subscriptions 
                (user_id, subscription_id, customer_id, product_id, status,
                 cancel_at_period_end, current_period_start, current_period_end,
                 last_webhook_ts, updated_at)
            VALUES 
                (:user_id, :subscription_id, :customer_id, :product_id, :status,
                 :cancel_at_period_end, :current_period_start, :current_period_end,
                 :webhook_ts, now())
            ON CONFLICT (user_id) DO UPDATE SET
                subscription_id = EXCLUDED.subscription_id,
                customer_id = EXCLUDED.customer_id,
                product_id = EXCLUDED.product_id,
                status = EXCLUDED.status,
                cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                current_period_start = EXCLUDED.current_period_start,
                current_period_end = EXCLUDED.current_period_end,
                last_webhook_ts = EXCLUDED.last_webhook_ts,
                updated_at = now()
            WHERE user_subscriptions.last_webhook_ts < EXCLUDED.last_webhook_ts
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
            }
        )
        
        # Determine if we should update role/periods
        # Only grant paid role for non-failed states.
        allowed_role_statuses = {"active", "cancelled"}
        should_update_role = status in allowed_role_statuses

        # Determine if we should reset credit_period_start
        # Reset on: new subscription, plan change (upgrade/downgrade)
        reset_credit_period = (is_new_subscription or is_plan_change) and should_update_role
        
        if should_update_role:
            if reset_credit_period:
                # Reset credit period to now (credits reset on plan change)
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
                        "role": role,
                        "period_start": current_period_start,
                        "customer_id": customer_id,
                    }
                )
                logger.info(
                    f"Applied subscription state for user {user_id}: role={role}, status={status}, credit_period RESET"
                )
            else:
                # Just update role and period_start, don't touch credit_period_start
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
                        "role": role,
                        "period_start": current_period_start,
                        "customer_id": customer_id,
                    }
                )
                logger.info(f"Applied subscription state for user {user_id}: role={role}, status={status}")
        else:
            # Keep role/periods unchanged for failed/pending states.
            await conn.execute(
                text("""
                UPDATE users
                SET dodo_customer_id = :customer_id
                WHERE id = :user_id
                """),
                {
                    "user_id": user_id,
                    "customer_id": customer_id,
                }
            )
            logger.info(
                f"Applied subscription state for user {user_id}: role unchanged, status={status}"
            )
    
    # Sync role to Firebase custom claims only when role updated
    if should_update_role:
        await _sync_firebase_role(user_id, role)


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
        
        # Update subscription status
        await conn.execute(
            text("""
            UPDATE user_subscriptions
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
            text("SELECT user_id FROM user_subscriptions WHERE subscription_id = :subscription_id"),
            {"subscription_id": subscription_id}
        )
        row = result.fetchone()
        return row[0] if row else None
