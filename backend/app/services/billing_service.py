"""Billing service for subscription management."""
import json
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from sqlalchemy import text

from app.billing.domain import (
    AccessStatus,
    BillingOperationStatus,
    BillingOperationType,
    BillingState,
    EntitlementStatus,
    PaymentStatus,
)
from app.core import logger, get_settings
from app.db.session import get_db_connection
from app.integrations.posthog_client import capture_event
from app.services import dodo_client

BILLING_ACTION_CHECKOUT = "checkout"
BILLING_ACTION_PREVIEW_CHANGE = "preview_change"
BILLING_ACTION_UPGRADE = "upgrade"
BILLING_ACTION_DOWNGRADE = "downgrade"
BILLING_ACTION_CANCEL = "cancel"
BILLING_ACTION_UNDO_CANCEL = "undo_cancel"
BILLING_ACTION_REACTIVATE = "reactivate"

ROLE_PRIORITY = {
    "free": 0,
    "creator": 1,
    "pro_research": 2,
}

STATE_TO_ALLOWED_ACTIONS = {
    "none": [BILLING_ACTION_CHECKOUT],
    "pending": [],
    "failed": [BILLING_ACTION_CHECKOUT],
    "expired": [BILLING_ACTION_CHECKOUT],
    "cancelled": [BILLING_ACTION_CHECKOUT],
    "on_hold": [BILLING_ACTION_REACTIVATE],
    "trial_failed": [BILLING_ACTION_REACTIVATE],
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

    hold_reason = (subscription.get("hold_reason") or "").lower()
    if hold_reason == "trial_failed":
        return "trial_failed"

    explicit_state = (subscription.get("billing_state") or "").lower()
    if explicit_state:
        return explicit_state

    status = (subscription.get("status") or "").lower()
    cancel_at_period_end = bool(subscription.get("cancel_at_period_end"))

    if status == "active":
        return "active_cancel_scheduled" if cancel_at_period_end else "active"
    if status in STATE_TO_ALLOWED_ACTIONS:
        return status
    return "none"


async def _has_prior_successful_paid_charge(conn, subscription_id: str) -> bool:
    """True when the subscription has at least one successful non-zero payment."""
    result = await conn.execute(
        text("""
        SELECT 1
        FROM billing_payments
        WHERE provider_subscription_id = :subscription_id
          AND status = 'paid'
          AND amount > 0
        LIMIT 1
        """),
        {"subscription_id": subscription_id},
    )
    return result.fetchone() is not None


async def _enrich_subscription_record(conn, subscription: dict) -> dict:
    """Apply local entitlement policy to a raw subscription record."""
    enriched = dict(subscription)
    status = (enriched.get("status") or "").lower()
    current_period_end = _parse_datetime(enriched.get("current_period_end"))
    now = datetime.now(timezone.utc)
    enriched["has_successful_paid_charge"] = await _has_prior_successful_paid_charge(
        conn,
        enriched["subscription_id"],
    )

    hold_reason = None
    if status == "on_hold":
        if enriched["has_successful_paid_charge"]:
            hold_reason = "grace" if current_period_end and current_period_end > now else "ended"
        else:
            hold_reason = "trial_failed"

        enriched["hold_reason"] = hold_reason
        if hold_reason == "trial_failed":
            enriched["access_status"] = AccessStatus.ENDED.value
            enriched["entitlement_status"] = EntitlementStatus.ENDED.value
        elif hold_reason == "grace":
            enriched["access_status"] = AccessStatus.GRACE.value
            enriched["entitlement_status"] = EntitlementStatus.EFFECTIVE.value
        else:
            enriched["access_status"] = AccessStatus.RESTRICTED.value
            enriched["entitlement_status"] = EntitlementStatus.ENDED.value
    return enriched


def _subscription_grants_paid_role(subscription: Optional[dict]) -> bool:
    """Whether a subscription should grant the user a paid role."""
    if not subscription:
        return False
    status = (subscription.get("status") or "").lower()
    access_status = (subscription.get("access_status") or "").lower()
    if status == "active":
        return True
    if status == "on_hold":
        return access_status == AccessStatus.GRACE.value
    if status == "cancelled":
        period_end = _parse_datetime(subscription.get("current_period_end"))
        return bool(period_end and period_end > datetime.now(timezone.utc))
    return False


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


async def _get_product_trial_fields(
    product_id: Optional[str],
    current_period_start: Optional[datetime],
    current_period_end: Optional[datetime],
) -> dict[str, Any]:
    """Compute persisted trial fields from product metadata and billing dates."""
    if not product_id:
        return {
            "trial_period_days": None,
            "trial_ends_at": None,
            "first_charge_at": None,
        }

    product = dodo_client.get_product_by_id(product_id)
    if not product:
        await dodo_client.get_products()
        product = dodo_client.get_product_by_id(product_id)

    trial_period_days = int((product or {}).get("trial_period_days") or 0)
    if trial_period_days <= 0 or current_period_start is None:
        return {
            "trial_period_days": None,
            "trial_ends_at": None,
            "first_charge_at": None,
        }

    trial_ends_at = current_period_start + timedelta(days=trial_period_days)
    if current_period_end and current_period_end < trial_ends_at:
        trial_ends_at = current_period_end

    return {
        "trial_period_days": trial_period_days,
        "trial_ends_at": trial_ends_at,
        "first_charge_at": trial_ends_at,
    }


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
    current_operation = await get_current_billing_operation(
        user_id=user_id,
        subscription_id=(subscription or {}).get("subscription_id"),
    )
    payment_issue = await get_current_payment_issue(
        subscription_id=(subscription or {}).get("subscription_id")
    )
    history = await get_billing_history(
        user_id=user_id,
        subscription_id=(subscription or {}).get("subscription_id"),
        limit=10,
    )
    trial_summary = await get_trial_summary((subscription or {}).get("subscription_id"))

    if subscription:
        db_role = subscription.get("db_role", "free")
    else:
        db_role = await _get_user_role(user_id)

    has_subscription = state in {"active", "active_cancel_scheduled", "on_hold", "cancelled"}
    if state == "trial_failed":
        has_subscription = True
    access_status = (subscription or {}).get("access_status")
    access_granted = access_status in {
        AccessStatus.ACTIVE.value,
        AccessStatus.GRACE.value,
    } or cancelled_with_access

    subscription_data = dict(subscription) if subscription else {}
    subscription_data.pop("db_role", None)
    pending_change = None
    if subscription_data.get("pending_change_type") == "downgrade":
        target_product_id = subscription_data.get("pending_target_product_id")
        pending_change = {
            "type": "downgrade",
            "status": "scheduled",
            "target_product_id": target_product_id,
            "target_role": await _get_product_role(target_product_id),
            "effective_at": subscription_data.get("pending_effective_at") or subscription_data.get("current_period_end"),
            "created_at": subscription_data.get("last_webhook_ts"),
        }
    elif subscription_data.get("pending_change_type"):
        pending_change = {
            "type": subscription_data.get("pending_change_type"),
            "status": "pending",
            "target_product_id": subscription_data.get("pending_target_product_id"),
            "effective_at": subscription_data.get("pending_effective_at") or subscription_data.get("current_period_end"),
        }

    return {
        "role": db_role,
        "billing_state": state,
        "allowed_actions": allowed_actions,
        "has_subscription": has_subscription,
        "access_granted": access_granted,
        "cancelled_with_access": cancelled_with_access,
        "can_manage_billing": bool((subscription or {}).get("customer_id")),
        "summary": {
            "billing_state": state,
            "subscription_status": subscription_data.get("status"),
            "payment_status": subscription_data.get("payment_status"),
            "access_status": subscription_data.get("access_status"),
            "entitlement_status": subscription_data.get("entitlement_status"),
            "effective_product_id": subscription_data.get("effective_product_id") or subscription_data.get("product_id"),
            "provider_product_id": subscription_data.get("provider_product_id"),
            "current_period_start": subscription_data.get("current_period_start"),
            "current_period_end": subscription_data.get("current_period_end"),
            "cancel_at_period_end": subscription_data.get("cancel_at_period_end", False),
            "renews_at": None if subscription_data.get("cancel_at_period_end") else subscription_data.get("current_period_end"),
            "ends_at": subscription_data.get("current_period_end") if subscription_data.get("cancel_at_period_end") or state in {"cancelled", "expired"} else None,
            "is_trialing": trial_summary.get("is_trialing", False),
            "trial_ends_at": trial_summary.get("trial_ends_at"),
            "first_charge_at": trial_summary.get("first_charge_at"),
            "trial_period_days": trial_summary.get("trial_period_days"),
            "on_hold_reason": subscription_data.get("hold_reason"),
        },
        "pending_change": pending_change,
        "current_operation": current_operation,
        "payment_issue": payment_issue,
        "history": history,
        **subscription_data,
    }


async def get_trial_summary(subscription_id: Optional[str]) -> dict:
    """Infer trial status from persisted billing subscription data."""
    if not subscription_id:
        return {
            "is_trialing": False,
            "trial_ends_at": None,
            "first_charge_at": None,
            "trial_period_days": 0,
        }

    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            SELECT
                status,
                access_status,
                trial_period_days,
                trial_ends_at,
                first_charge_at
            FROM billing_subscriptions
            WHERE subscription_id = :subscription_id
            """),
            {"subscription_id": subscription_id},
        )
        row = result.fetchone()
        if not row:
            return {
                "is_trialing": False,
                "trial_ends_at": None,
                "first_charge_at": None,
                "trial_period_days": 0,
            }

        status = (row[0] or "").lower()
        access_status = (row[1] or "").lower()
        trial_period_days = int(row[2] or 0)
        trial_ends_at = row[3]
        first_charge_at = row[4]
        now = datetime.now(timezone.utc)
        has_successful_paid_charge = await _has_prior_successful_paid_charge(conn, subscription_id)

        is_trialing = bool(
            trial_period_days > 0
            and trial_ends_at
            and now < trial_ends_at
            and status in {"pending", "active"}
            and access_status in {AccessStatus.ACTIVE.value, AccessStatus.GRACE.value, ""}
            and not has_successful_paid_charge
        )

        return {
            "is_trialing": is_trialing,
            "trial_ends_at": trial_ends_at.isoformat() if trial_ends_at else None,
            "first_charge_at": first_charge_at.isoformat() if first_charge_at else None,
            "trial_period_days": trial_period_days,
        }


async def get_current_trial_status_for_user(user_id: UUID) -> dict:
    """
    Infer the current user's trial state from the effective subscription.
    This reuses provider-backed trial inference so trial end remains correct after
    the first paid billing period starts.
    """
    subscription = await get_user_subscription(user_id)
    if not subscription or not _subscription_grants_paid_role(subscription):
        return {
            "is_trialing": False,
            "trial_ends_at": None,
            "first_charge_at": None,
            "trial_period_days": 0,
        }

    trial_period_days = int(subscription.get("trial_period_days") or 0)
    trial_ends_at = _parse_datetime(subscription.get("trial_ends_at"))
    first_charge_at = _parse_datetime(subscription.get("first_charge_at"))
    now = datetime.now(timezone.utc)

    is_trialing = bool(
        trial_period_days > 0
        and trial_ends_at
        and now < trial_ends_at
        and _subscription_grants_paid_role(subscription)
        and not subscription.get("has_successful_paid_charge", False)
    )

    return {
        "is_trialing": is_trialing,
        "trial_ends_at": trial_ends_at.isoformat() if trial_ends_at else None,
        "first_charge_at": first_charge_at.isoformat() if first_charge_at else None,
        "trial_period_days": trial_period_days,
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
    await require_allowed_action(user_id, BILLING_ACTION_CHECKOUT)

    operation_id = await create_billing_operation(
        user_id=user_id,
        operation_type=BillingOperationType.CHECKOUT_START.value,
        requested_to_product_id=product_id,
        status=BillingOperationStatus.PENDING.value,
        ui_status="awaiting_webhook",
        metadata={"source": "backend_billing_checkout"},
    )

    try:
        session = await dodo_client.create_checkout_session(
            product_id=product_id,
            customer_id=dodo_customer_id,
            customer_email=email if not dodo_customer_id else None,
            metadata={"user_id": str(user_id), "operation_id": operation_id},
        )

        try:
            await attach_operation_external_refs(
                operation_id=operation_id,
                metadata_patch={"checkout_session_id": session.get("session_id")},
            )
        except Exception as e:
            logger.warning(f"Failed to attach checkout refs for operation {operation_id}: {e}")

        # Track checkout session created for pricing funnel
        try:
            capture_event(
                distinct_id=str(user_id),
                event="checkout_created",
                properties={
                    "product_id": product_id,
                    "session_id": session.get("session_id"),
                    "source": "backend_billing",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to capture checkout telemetry for operation {operation_id}: {e}")

        return {**session, "operation_id": operation_id}
    except Exception as e:
        await mark_billing_operation_failed(operation_id, str(e))
        raise


async def preview_plan_change_for_user(
    user_id: UUID,
    target_product_id: str,
) -> dict:
    """Preview a plan change using backend-owned transition policy."""
    context = await require_allowed_action(user_id, BILLING_ACTION_PREVIEW_CHANGE)
    subscription_id = context.get("subscription_id")
    current_product_id = context.get("product_id")
    if not subscription_id or not current_product_id:
        raise ValueError("No active subscription found")

    products = await dodo_client.get_products()
    classification = await classify_plan_change(
        current_product_id=current_product_id,
        target_product_id=target_product_id,
        products=products,
    )

    if classification["transition_type"] == "upgrade":
        preview = await dodo_client.preview_change_plan(
            subscription_id=subscription_id,
            product_id=target_product_id,
            proration_mode=classification["proration_mode"],
            on_payment_failure=classification["on_payment_failure"],
        )
        immediate_charge = preview.get("immediate_charge")
        summary = preview.get("summary") or getattr(immediate_charge, "summary", None)
        effective_at = getattr(immediate_charge, "effective_at", None)
    else:
        immediate_charge = {
            "effective_at": context.get("current_period_end"),
            "line_items": [],
            "summary": {
                "currency": classification["target_plan"]["currency"],
                "customer_credits": 0,
                "settlement_amount": 0,
                "total_amount": 0,
            },
        }
        summary = immediate_charge["summary"]
        preview = {
            "immediate_charge": immediate_charge,
            "credit_amount": 0,
            "charge_amount": 0,
            "summary": summary,
            "new_plan": None,
            "raw": None,
        }
        effective_at = immediate_charge["effective_at"]

    return {
        **preview,
        "transition_type": classification["transition_type"],
        "proration_mode": classification["proration_mode"],
        "effective_at": effective_at,
        "current_plan": classification["current_plan"],
        "target_plan": classification["target_plan"],
        "cross_interval": classification["cross_interval"],
        "requires_payment_confirmation": classification["transition_type"] == "upgrade",
    }


async def create_billing_portal_session(user_id: UUID) -> dict:
    """Create a customer portal session for the current user."""
    customer_id = await get_user_dodo_customer_id(user_id)
    if not customer_id:
        raise ValueError("No billing customer found")
    return await dodo_client.create_customer_portal_session(customer_id)


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
                subscription_id, customer_id, product_id, effective_product_id, status,
                billing_state, payment_status, access_status, entitlement_status,
                pending_change_type, pending_target_product_id, pending_effective_at,
                cancel_at_period_end, current_period_start, current_period_end, last_webhook_ts,
                trial_period_days, trial_ends_at, first_charge_at
            FROM billing_subscriptions
            WHERE user_id = :user_id
            ORDER BY last_webhook_ts DESC
            """),
            {"user_id": user_id},
        )
        for row in result.fetchall():
            subscription = {
                "subscription_id": row[0],
                "customer_id": row[1],
                "provider_product_id": row[2],
                "product_id": row[3] or row[2],
                "effective_product_id": row[3] or row[2],
                "status": row[4],
                "billing_state": row[5],
                "payment_status": row[6],
                "access_status": row[7],
                "entitlement_status": row[8],
                "pending_change_type": row[9],
                "pending_target_product_id": row[10],
                "pending_effective_at": row[11].isoformat() if row[11] else None,
                "cancel_at_period_end": row[12],
                "current_period_start": row[13].isoformat() if row[13] else None,
                "current_period_end": row[14].isoformat() if row[14] else None,
                "last_webhook_ts": row[15].isoformat() if row[15] else None,
                "trial_period_days": int(row[16] or 0),
                "trial_ends_at": row[17].isoformat() if row[17] else None,
                "first_charge_at": row[18].isoformat() if row[18] else None,
            }
            subscriptions.append(await _enrich_subscription_record(conn, subscription))

        subscription = _pick_winner_subscription(subscriptions)
        if not subscription:
            return None
        subscription["db_role"] = db_role

        return subscription


async def _get_product_role(product_id: Optional[str]) -> str:
    """Resolve app role for a Dodo product id."""
    if not product_id:
        return "free"
    product = dodo_client.get_product_by_id(product_id)
    if not product:
        await dodo_client.get_products()
        product = dodo_client.get_product_by_id(product_id)
    return product["metadata"].get("app_role", "free") if product else "free"


def _build_cycle_map(products: list[dict]) -> dict[str, str]:
    """Infer billing cadence per product from same-role pricing."""
    role_groups: dict[str, list[dict]] = {}
    cycle_map: dict[str, str] = {}

    for product in products:
        role = (product.get("metadata") or {}).get("app_role", "free")
        role_groups.setdefault(role, []).append(product)

    for role_products in role_groups.values():
        if len(role_products) == 1:
            cycle_map[role_products[0]["product_id"]] = "monthly"
            continue
        ordered = sorted(role_products, key=lambda item: item.get("price", 0))
        cycle_map[ordered[0]["product_id"]] = "monthly"
        cycle_map[ordered[-1]["product_id"]] = "annual"
        for middle in ordered[1:-1]:
            cycle_map[middle["product_id"]] = "monthly"

    return cycle_map


def _plan_snapshot(product: Optional[dict], cycle_map: dict[str, str]) -> dict:
    if not product:
        return {
            "product_id": None,
            "name": None,
            "price": 0,
            "currency": "USD",
            "role": "free",
            "credits": 0,
            "cycle": None,
        }
    metadata = product.get("metadata") or {}
    product_id = product.get("product_id")
    return {
        "product_id": product_id,
        "name": product.get("name"),
        "price": product.get("price", 0),
        "currency": product.get("currency", "USD"),
        "role": metadata.get("app_role", "free"),
        "credits": int(metadata.get("credits", 0) or 0),
        "cycle": cycle_map.get(product_id),
    }


async def classify_plan_change(
    current_product_id: str,
    target_product_id: str,
    products: Optional[list[dict]] = None,
) -> dict:
    """Classify a subscription transition and choose its billing policy."""
    products = products or await dodo_client.get_products()
    product_index = {product["product_id"]: product for product in products}
    cycle_map = _build_cycle_map(products)

    current_product = product_index.get(current_product_id)
    target_product = product_index.get(target_product_id)
    if not target_product:
        raise ValueError(f"Product {target_product_id} not found")
    if not current_product:
        raise ValueError(f"Current product {current_product_id} not found")
    if current_product_id == target_product_id:
        raise ValueError("Target plan matches the current plan.")

    current_plan = _plan_snapshot(current_product, cycle_map)
    target_plan = _plan_snapshot(target_product, cycle_map)

    current_role_rank = ROLE_PRIORITY.get(current_plan["role"], 0)
    target_role_rank = ROLE_PRIORITY.get(target_plan["role"], 0)
    same_role = current_plan["role"] == target_plan["role"]
    cross_interval = (
        current_plan["cycle"] is not None
        and target_plan["cycle"] is not None
        and current_plan["cycle"] != target_plan["cycle"]
    )

    if target_role_rank > current_role_rank:
        transition_type = "upgrade"
    elif target_role_rank < current_role_rank:
        transition_type = "downgrade"
    elif target_plan["price"] > current_plan["price"]:
        transition_type = "upgrade"
    elif target_plan["price"] < current_plan["price"]:
        transition_type = "downgrade"
    else:
        raise ValueError("Unable to classify the requested plan change.")

    if transition_type == "upgrade":
        proration_mode = "prorated_immediately"
        effective_at = "immediately"
        on_payment_failure = "prevent_change"
    else:
        proration_mode = "do_not_bill"
        effective_at = "next_billing_date"
        on_payment_failure = None

    return {
        "transition_type": transition_type,
        "effective_at": effective_at,
        "proration_mode": proration_mode,
        "on_payment_failure": on_payment_failure,
        "cross_interval": cross_interval,
        "same_role": same_role,
        "current_plan": current_plan,
        "target_plan": target_plan,
    }


async def _set_subscription_pending_change(
    subscription_id: str,
    change_type: Optional[str],
    target_product_id: Optional[str],
    effective_at: Optional[Any],
) -> None:
    """Persist pending change state on the canonical subscription row."""
    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            UPDATE billing_subscriptions
            SET pending_change_type = :change_type,
                pending_target_product_id = :target_product_id,
                pending_effective_at = :effective_at,
                updated_at = now()
            WHERE subscription_id = :subscription_id
            """),
            {
                "subscription_id": subscription_id,
                "change_type": change_type,
                "target_product_id": target_product_id,
                "effective_at": effective_at,
            },
        )


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
    
    products = await dodo_client.get_products()
    classification = await classify_plan_change(
        current_product_id=current_product_id,
        target_product_id=target_product_id,
        products=products,
    )
    if classification["transition_type"] != "upgrade":
        raise ValueError("Target plan must be an upgrade. Use the downgrade flow for end-of-cycle changes.")
    
    # Clear any scheduled downgrade before an immediate upgrade.
    await cancel_pending_downgrade(user_id, record_operation=False)

    operation_id = await create_billing_operation(
        user_id=user_id,
        operation_type=BillingOperationType.UPGRADE_REQUEST.value,
        provider_subscription_id=subscription_id,
        requested_from_product_id=current_product_id,
        requested_to_product_id=target_product_id,
        status=BillingOperationStatus.PENDING.value,
        ui_status="awaiting_webhook",
        metadata={
            "source": "backend_billing_upgrade",
            "proration_mode": classification["proration_mode"],
            "cross_interval": classification["cross_interval"],
        },
    )
    
    try:
        result = await dodo_client.change_plan(
            subscription_id=subscription_id,
            product_id=target_product_id,
            proration_mode=classification["proration_mode"],
            metadata={"operation_id": operation_id},
            on_payment_failure=classification["on_payment_failure"],
        )
    except Exception as exc:
        logger.warning(
            "Upgrade payment/change-plan failed for user %s subscription %s target %s: %s",
            user_id,
            subscription_id,
            target_product_id,
            exc,
        )

        try:
            recovery = await dodo_client.update_payment_method(
                subscription_id=subscription_id,
                return_url=get_settings().FRONTEND_RETURN_URL,
            )
        except Exception as recovery_exc:
            await mark_billing_operation_failed(operation_id, str(exc))
            logger.error(
                "Upgrade recovery link creation failed for user %s subscription %s: %s",
                user_id,
                subscription_id,
                recovery_exc,
            )
            raise exc

        await _set_billing_operation_waiting_for_payment(
            operation_id=operation_id,
            failure_reason=str(exc),
            metadata_patch={
                "payment_recovery": True,
                "recovery_payment_id": recovery.get("payment_id"),
            },
        )
        return {
            "success": False,
            "operation_id": operation_id,
            "transition_type": classification["transition_type"],
            "status": "payment_action_required",
            "payment_link": recovery.get("payment_link"),
            "message": "Payment failed while processing the upgrade. Complete payment to finish upgrading.",
        }
    
    logger.info(f"Upgrade initiated for user {user_id}: {current_product_id} -> {target_product_id}")
    return {
        **result,
        "operation_id": operation_id,
        "transition_type": classification["transition_type"],
        "status": "pending_payment_confirmation",
    }


async def request_downgrade(
    user_id: UUID,
    target_product_id: str,
) -> dict:
    """
    Request a downgrade at end of billing cycle.
    Stores the pending change on the canonical subscription row.
    """
    context = await require_allowed_action(user_id, BILLING_ACTION_DOWNGRADE)
    subscription_id = context.get("subscription_id")
    current_product_id = context.get("product_id")
    if not subscription_id or not current_product_id:
        raise ValueError("No active subscription found")
    
    products = await dodo_client.get_products()
    classification = await classify_plan_change(
        current_product_id=current_product_id,
        target_product_id=target_product_id,
        products=products,
    )
    if classification["transition_type"] != "downgrade":
        raise ValueError("Target plan must be a downgrade. Immediate moves belong in the upgrade flow.")
    
    # Cancel any existing pending downgrade.
    await cancel_pending_downgrade(user_id, record_operation=False)
    await dodo_client.schedule_plan_change(
        subscription_id=subscription_id,
        product_id=target_product_id,
        metadata={"scheduled_by": "backend_billing_downgrade"},
    )
    await _set_subscription_pending_change(
        subscription_id=subscription_id,
        change_type="downgrade",
        target_product_id=target_product_id,
        effective_at=context.get("current_period_end"),
    )

    await create_billing_operation(
        user_id=user_id,
        operation_type=BillingOperationType.DOWNGRADE_SCHEDULE.value,
        provider_subscription_id=subscription_id,
        requested_from_product_id=current_product_id,
        requested_to_product_id=target_product_id,
        status=BillingOperationStatus.COMPLETED.value,
        ui_status="completed",
        metadata={
            "source": "backend_billing_downgrade_schedule",
            "proration_mode": classification["proration_mode"],
        },
    )
    
    logger.info(f"Downgrade scheduled for user {user_id}: {current_product_id} -> {target_product_id} at end of cycle")
    
    return {
        "message": "Downgrade scheduled for end of billing cycle",
        "effective_at": context.get("current_period_end"),
        "target_product_id": target_product_id,
        "target_role": classification["target_plan"]["role"],
    }


async def cancel_pending_downgrade(user_id: UUID, record_operation: bool = True) -> bool:
    """Cancel any pending downgrade for user."""
    context = await get_billing_context(user_id)
    subscription_id = context.get("subscription_id")
    current_product_id = context.get("product_id")
    target_product_id = None
    pending_change = context.get("pending_change") or {}
    if pending_change.get("type") == "downgrade":
        target_product_id = pending_change.get("target_product_id")
        if subscription_id:
            try:
                await dodo_client.cancel_scheduled_change(subscription_id)
            except Exception as e:
                logger.warning(f"Failed to cancel provider scheduled change for {subscription_id}: {e}")

    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            UPDATE billing_subscriptions
            SET pending_change_type = NULL,
                pending_target_product_id = NULL,
                pending_effective_at = NULL,
                updated_at = now()
            WHERE user_id = :user_id
              AND pending_change_type = 'downgrade'
            """),
            {"user_id": user_id}
        )
        cancelled = result.rowcount > 0
        if cancelled:
            logger.info(f"Cancelled pending downgrade for user {user_id}")
    if cancelled and record_operation:
        await create_billing_operation(
            user_id=user_id,
            operation_type=BillingOperationType.DOWNGRADE_CANCEL.value,
            provider_subscription_id=subscription_id,
            requested_from_product_id=current_product_id,
            requested_to_product_id=target_product_id,
            status=BillingOperationStatus.COMPLETED.value,
            ui_status="completed",
            metadata={"source": "backend_billing_downgrade_cancel"},
        )
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
    
    # Clear any scheduled downgrade since cancellation supersedes it.
    await cancel_pending_downgrade(user_id, record_operation=False)
    
    # Set cancel_at_period_end via Dodo
    await dodo_client.set_cancel_at_period_end(
        subscription_id=subscription_id,
        cancel=True,
    )

    await create_billing_operation(
        user_id=user_id,
        operation_type=BillingOperationType.CANCEL_SCHEDULE.value,
        provider_subscription_id=subscription_id,
        requested_from_product_id=context.get("product_id"),
        status=BillingOperationStatus.COMPLETED.value,
        ui_status="completed",
        metadata={"source": "backend_billing_cancel"},
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

    await create_billing_operation(
        user_id=user_id,
        operation_type=BillingOperationType.CANCEL_UNDO.value,
        provider_subscription_id=subscription_id,
        requested_from_product_id=context.get("product_id"),
        status=BillingOperationStatus.COMPLETED.value,
        ui_status="completed",
        metadata={"source": "backend_billing_undo_cancel"},
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
) -> None:
    """
    Apply subscription state from webhook.
    Updates canonical subscription history and recomputes winner-derived user state.

    is_new_subscription: Set credit_period_start for a newly activated subscription.
    """
    derived = None
    winner = None
    new_role = "free"

    async with get_db_connection() as conn:
        user_period_result = await conn.execute(
            text("""
            SELECT current_period_start
            FROM users
            WHERE id = :user_id
            """),
            {"user_id": user_id},
        )
        user_period_row = user_period_result.fetchone()
        existing_current_period_start = user_period_row[0] if user_period_row else None

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

        derived = await _derive_subscription_fields(
            conn=conn,
            subscription_id=subscription_id,
            incoming_product_id=product_id,
            status=status,
            cancel_at_period_end=cancel_at_period_end,
            current_period_end=current_period_end,
        )
        trial_fields = await _get_product_trial_fields(
            derived["effective_product_id"] or product_id,
            current_period_start,
            current_period_end,
        )

        # Canonical per-subscription history table (new model).
        upsert_result = await conn.execute(
            text("""
            INSERT INTO billing_subscriptions
                (user_id, subscription_id, customer_id, product_id, status,
                 effective_product_id, billing_state, payment_status, access_status,
                 entitlement_status, pending_change_type, pending_target_product_id,
                 pending_effective_at, last_payment_status, last_paid_at,
                 trial_period_days, trial_ends_at, first_charge_at,
                 cancel_at_period_end, current_period_start, current_period_end,
                 last_webhook_ts, updated_at)
            VALUES
                (:user_id, :subscription_id, :customer_id, :product_id, :status,
                 :effective_product_id, :billing_state, :payment_status, :access_status,
                 :entitlement_status, :pending_change_type, :pending_target_product_id,
                 :pending_effective_at, :last_payment_status, :last_paid_at,
                 :trial_period_days, :trial_ends_at, :first_charge_at,
                 :cancel_at_period_end, :current_period_start, :current_period_end,
                 :webhook_ts, now())
            ON CONFLICT (subscription_id) DO UPDATE SET
                -- Keep subscription owner immutable once first linked.
                user_id = billing_subscriptions.user_id,
                customer_id = EXCLUDED.customer_id,
                product_id = EXCLUDED.product_id,
                effective_product_id = EXCLUDED.effective_product_id,
                status = EXCLUDED.status,
                billing_state = EXCLUDED.billing_state,
                payment_status = EXCLUDED.payment_status,
                access_status = EXCLUDED.access_status,
                entitlement_status = EXCLUDED.entitlement_status,
                pending_change_type = EXCLUDED.pending_change_type,
                pending_target_product_id = EXCLUDED.pending_target_product_id,
                pending_effective_at = EXCLUDED.pending_effective_at,
                last_payment_status = EXCLUDED.last_payment_status,
                last_paid_at = EXCLUDED.last_paid_at,
                trial_period_days = EXCLUDED.trial_period_days,
                trial_ends_at = EXCLUDED.trial_ends_at,
                first_charge_at = EXCLUDED.first_charge_at,
                cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                current_period_start = EXCLUDED.current_period_start,
                current_period_end = EXCLUDED.current_period_end,
                last_webhook_ts = EXCLUDED.last_webhook_ts,
                version = billing_subscriptions.version + 1,
                updated_at = now()
            WHERE billing_subscriptions.last_webhook_ts < EXCLUDED.last_webhook_ts
            RETURNING subscription_id
            """),
            {
                "user_id": user_id,
                "subscription_id": subscription_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "effective_product_id": derived["effective_product_id"],
                "status": status,
                "billing_state": derived["billing_state"],
                "payment_status": derived["payment_status"],
                "access_status": derived["access_status"],
                "entitlement_status": derived["entitlement_status"],
                "pending_change_type": derived["pending_change_type"],
                "pending_target_product_id": derived["pending_target_product_id"],
                "pending_effective_at": derived["pending_effective_at"],
                "last_payment_status": derived["last_payment_status"],
                "last_paid_at": derived["last_paid_at"],
                "trial_period_days": trial_fields["trial_period_days"],
                "trial_ends_at": trial_fields["trial_ends_at"],
                "first_charge_at": trial_fields["first_charge_at"],
                "cancel_at_period_end": cancel_at_period_end,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
                "webhook_ts": webhook_ts,
            },
        )
        upsert_row = upsert_result.fetchone()
        if not upsert_row:
            logger.info(
                "Skipping stale subscription webhook for %s: status=%s webhook_ts=%s",
                subscription_id,
                status,
                webhook_ts.isoformat() if isinstance(webhook_ts, datetime) else webhook_ts,
            )
            return

        # Recompute winner from all subscriptions for this user.
        winner_result = await conn.execute(
            text("""
            SELECT
                subscription_id, customer_id, product_id, effective_product_id, status,
                billing_state, payment_status, access_status, entitlement_status,
                cancel_at_period_end, current_period_start, current_period_end, last_webhook_ts,
                trial_period_days, trial_ends_at, first_charge_at
            FROM billing_subscriptions
            WHERE user_id = :user_id
            ORDER BY last_webhook_ts DESC
            """),
            {"user_id": user_id},
        )
        candidates = []
        for row in winner_result.fetchall():
            candidate = {
                "subscription_id": row[0],
                "customer_id": row[1],
                "provider_product_id": row[2],
                "product_id": row[3] or row[2],
                "effective_product_id": row[3] or row[2],
                "status": row[4],
                "billing_state": row[5],
                "payment_status": row[6],
                "access_status": row[7],
                "entitlement_status": row[8],
                "cancel_at_period_end": row[9],
                "current_period_start": row[10].isoformat() if row[10] else None,
                "current_period_end": row[11].isoformat() if row[11] else None,
                "last_webhook_ts": row[12].isoformat() if row[12] else None,
                "trial_period_days": int(row[13] or 0),
                "trial_ends_at": row[14].isoformat() if row[14] else None,
                "first_charge_at": row[15].isoformat() if row[15] else None,
            }
            candidates.append(await _enrich_subscription_record(conn, candidate))
        winner = _pick_winner_subscription(candidates)

        period_start_to_set = datetime.now(timezone.utc)
        customer_id_to_set = customer_id

        if winner and _subscription_grants_paid_role(winner):
            winner_product = dodo_client.get_product_by_id(winner["effective_product_id"])
            if not winner_product:
                await dodo_client.get_products()
                winner_product = dodo_client.get_product_by_id(winner["effective_product_id"])
            new_role = winner_product["metadata"].get("app_role", "free") if winner_product else "free"
            period_start_to_set = _parse_datetime(winner.get("current_period_start")) or datetime.now(timezone.utc)
            customer_id_to_set = winner.get("customer_id") or customer_id
        elif winner:
            customer_id_to_set = winner.get("customer_id") or customer_id

        reset_credit_period = (
            winner
            and winner.get("subscription_id") == subscription_id
            and new_role != "free"
            and period_start_to_set is not None
            and (
                existing_current_period_start is None
                or (
                    existing_current_period_start.replace(tzinfo=timezone.utc)
                    if existing_current_period_start.tzinfo is None
                    else existing_current_period_start.astimezone(timezone.utc)
                ) != period_start_to_set.astimezone(timezone.utc)
            )
        )

        if reset_credit_period:
            await conn.execute(
                text("""
                UPDATE users
                SET role = :role,
                    current_period_start = :period_start,
                    credit_period_start = :period_start,
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
    await _reconcile_operation_state(
        user_id=user_id,
        subscription_id=subscription_id,
        status=status,
        effective_product_id=derived["effective_product_id"] if derived else product_id,
        current_product_id=product_id,
    )
    await append_billing_audit_log(
        user_id=user_id,
        subscription_id=subscription_id,
        operation_id=None,
        event_name=f"subscription.{status}",
        payload={
            "provider_product_id": product_id,
            "effective_product_id": derived["effective_product_id"] if derived else product_id,
            "billing_state": derived["billing_state"] if derived else None,
            "payment_status": derived["payment_status"] if derived else None,
            "access_status": derived["access_status"] if derived else None,
            "cancel_at_period_end": cancel_at_period_end,
            "current_period_start": current_period_start.isoformat() if isinstance(current_period_start, datetime) else current_period_start,
            "current_period_end": current_period_end.isoformat() if isinstance(current_period_end, datetime) else current_period_end,
        },
    )
    logger.info(
        f"Applied subscription state for user {user_id}: incoming_status={status}, effective_product={derived['effective_product_id'] if derived else product_id}, winner={winner.get('subscription_id') if winner else 'none'}, role={new_role}"
    )


async def get_pending_downgrade(subscription_id: str) -> Optional[dict]:
    """Get pending downgrade for a subscription."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            SELECT user_id, pending_target_product_id, pending_effective_at
            FROM billing_subscriptions
            WHERE subscription_id = :subscription_id
              AND pending_change_type = 'downgrade'
            LIMIT 1
            """),
            {"subscription_id": subscription_id}
        )
        row = result.fetchone()
        
        if row:
            return {
                "id": subscription_id,
                "user_id": row[0],
                "target_product_id": row[1],
                "effective_at": row[2].isoformat() if row[2] else None,
            }
        return None


async def mark_pending_applied(subscription_id: str) -> None:
    """Clear the scheduled downgrade once the provider apply call has been issued."""
    await _set_subscription_pending_change(
        subscription_id=subscription_id,
        change_type=None,
        target_product_id=None,
        effective_at=None,
    )
    logger.info(f"Marked pending downgrade as applied for subscription {subscription_id}")


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
        user_period_result = await conn.execute(
            text("""
            SELECT current_period_start
            FROM users
            WHERE id = :user_id
            """),
            {"user_id": user_id},
        )
        user_period_row = user_period_result.fetchone()
        existing_current_period_start = user_period_row[0] if user_period_row else None

        result = await conn.execute(
            text("""
            SELECT
                subscription_id, customer_id, product_id, effective_product_id, status,
                billing_state, payment_status, access_status, entitlement_status,
                cancel_at_period_end, current_period_start, current_period_end, last_webhook_ts,
                trial_period_days, trial_ends_at, first_charge_at
            FROM billing_subscriptions
            WHERE user_id = :user_id
            ORDER BY last_webhook_ts DESC
            """),
            {"user_id": user_id},
        )
        subscriptions = []
        for row in result.fetchall():
            subscription = {
                "subscription_id": row[0],
                "customer_id": row[1],
                "provider_product_id": row[2],
                "product_id": row[3] or row[2],
                "effective_product_id": row[3] or row[2],
                "status": row[4],
                "billing_state": row[5],
                "payment_status": row[6],
                "access_status": row[7],
                "entitlement_status": row[8],
                "cancel_at_period_end": row[9],
                "current_period_start": row[10].isoformat() if row[10] else None,
                "current_period_end": row[11].isoformat() if row[11] else None,
                "last_webhook_ts": row[12].isoformat() if row[12] else None,
                "trial_period_days": int(row[13] or 0),
                "trial_ends_at": row[14].isoformat() if row[14] else None,
                "first_charge_at": row[15].isoformat() if row[15] else None,
            }
            subscriptions.append(await _enrich_subscription_record(conn, subscription))
        winner = _pick_winner_subscription(subscriptions)
        if winner and _subscription_grants_paid_role(winner):
            winner_product = dodo_client.get_product_by_id(winner["effective_product_id"])
            if not winner_product:
                await dodo_client.get_products()
                winner_product = dodo_client.get_product_by_id(winner["effective_product_id"])
            new_role = winner_product["metadata"].get("app_role", "free") if winner_product else "free"
            period_start_to_set = _parse_datetime(winner.get("current_period_start")) or datetime.now(timezone.utc)
            customer_id_to_set = winner.get("customer_id")
        elif winner:
            customer_id_to_set = winner.get("customer_id")

        should_reset_credit_period = (
            new_role != "free"
            and period_start_to_set is not None
            and (
                existing_current_period_start is None
                or (
                    existing_current_period_start.replace(tzinfo=timezone.utc)
                    if existing_current_period_start.tzinfo is None
                    else existing_current_period_start.astimezone(timezone.utc)
                ) != period_start_to_set.astimezone(timezone.utc)
            )
        )

        if should_reset_credit_period:
            await conn.execute(
                text("""
                UPDATE users
                SET role = :role,
                    current_period_start = :period_start,
                    credit_period_start = :period_start,
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
        else:
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


async def create_billing_operation(
    user_id: UUID,
    operation_type: str,
    provider_subscription_id: Optional[str] = None,
    requested_from_product_id: Optional[str] = None,
    requested_to_product_id: Optional[str] = None,
    status: str = BillingOperationStatus.PENDING.value,
    ui_status: str = "pending",
    metadata: Optional[dict] = None,
    idempotency_key: Optional[str] = None,
) -> str:
    """Create a durable billing operation record."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            INSERT INTO billing_operations (
                user_id, operation_type, provider_subscription_id,
                requested_from_product_id, requested_to_product_id,
                status, ui_status, metadata, idempotency_key
            )
            VALUES (
                :user_id, :operation_type, :provider_subscription_id,
                :requested_from_product_id, :requested_to_product_id,
                :status, :ui_status, CAST(:metadata AS jsonb), :idempotency_key
            )
            RETURNING id::text
            """),
            {
                "user_id": user_id,
                "operation_type": operation_type,
                "provider_subscription_id": provider_subscription_id,
                "requested_from_product_id": requested_from_product_id,
                "requested_to_product_id": requested_to_product_id,
                "status": status,
                "ui_status": ui_status,
                "metadata": json.dumps(metadata or {}),
                "idempotency_key": idempotency_key,
            },
        )
        row = result.fetchone()
    await append_billing_audit_log(
        user_id=user_id,
        subscription_id=provider_subscription_id,
        operation_id=row[0],
        event_name=f"operation.{operation_type}",
        payload={
            "status": status,
            "ui_status": ui_status,
            "requested_from_product_id": requested_from_product_id,
            "requested_to_product_id": requested_to_product_id,
            "metadata": metadata or {},
        },
    )
    return row[0]


async def attach_operation_external_refs(operation_id: str, metadata_patch: dict) -> None:
    """Patch operation metadata without disturbing prior keys."""
    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            UPDATE billing_operations
            SET metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata_patch AS jsonb),
                updated_at = now()
            WHERE id = CAST(:operation_id AS uuid)
            """),
            {"operation_id": operation_id, "metadata_patch": json.dumps(metadata_patch)},
        )
    await append_billing_audit_log(
        user_id=None,
        subscription_id=None,
        operation_id=operation_id,
        event_name="operation.metadata_updated",
        payload=metadata_patch,
    )


async def mark_billing_operation_failed(operation_id: str, failure_reason: str) -> None:
    """Mark a billing operation as failed outside webhook reconciliation."""
    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            UPDATE billing_operations
            SET status = 'failed',
                ui_status = 'failed',
                failure_reason = :failure_reason,
                updated_at = now()
            WHERE id = CAST(:operation_id AS uuid)
            """),
            {
                "operation_id": operation_id,
                "failure_reason": failure_reason,
            },
        )
    await append_billing_audit_log(
        user_id=None,
        subscription_id=None,
        operation_id=operation_id,
        event_name="operation.failed",
        payload={"failure_reason": failure_reason},
    )


async def _set_billing_operation_waiting_for_payment(
    operation_id: str,
    failure_reason: str,
    metadata_patch: Optional[dict] = None,
) -> None:
    """Mark a billing operation as awaiting explicit payment recovery."""
    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            UPDATE billing_operations
            SET status = 'pending',
                ui_status = 'requires_action',
                failure_reason = :failure_reason,
                metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata_patch AS jsonb),
                updated_at = now()
            WHERE id = CAST(:operation_id AS uuid)
            """),
            {
                "operation_id": operation_id,
                "failure_reason": failure_reason,
                "metadata_patch": json.dumps(metadata_patch or {}),
            },
        )
    await append_billing_audit_log(
        user_id=None,
        subscription_id=None,
        operation_id=operation_id,
        event_name="operation.requires_action",
        payload={
            "failure_reason": failure_reason,
            "metadata": metadata_patch or {},
        },
    )


async def record_webhook_inbox_event(
    webhook_id: str,
    event_type: str,
    subscription_id: Optional[str],
    payload: dict,
    event_ts: Optional[datetime] = None,
) -> bool:
    """Store webhook in the durable inbox. Returns True if newly inserted."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            INSERT INTO billing_webhook_inbox (
                webhook_id, event_type, provider_subscription_id, payload, event_ts
            )
            VALUES (
                :webhook_id, :event_type, :subscription_id, CAST(:payload AS jsonb), :event_ts
            )
            ON CONFLICT (provider, webhook_id) DO NOTHING
            RETURNING id
            """),
            {
                "webhook_id": webhook_id,
                "event_type": event_type,
                "subscription_id": subscription_id,
                "payload": json.dumps(payload),
                "event_ts": event_ts,
            },
        )
        return result.fetchone() is not None


async def mark_webhook_inbox_status(webhook_id: str, processing_status: str, error_message: Optional[str] = None) -> None:
    """Update webhook inbox processing result."""
    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            UPDATE billing_webhook_inbox
            SET processing_status = :processing_status,
                error_message = :error_message,
                processed_at = now()
            WHERE provider = 'dodo' AND webhook_id = :webhook_id
            """),
            {
                "processing_status": processing_status,
                "error_message": error_message,
                "webhook_id": webhook_id,
            },
        )


async def record_payment_event(
    payment_id: str,
    subscription_id: Optional[str],
    status: str,
    amount: int = 0,
    currency: str = "USD",
    failure_code: Optional[str] = None,
    failure_message: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """Upsert payment lifecycle data from webhooks."""
    if not payment_id:
        return

    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            INSERT INTO billing_payments (
                provider_payment_id, provider_subscription_id, status, amount, currency,
                failure_code, failure_message, metadata, paid_at
            )
            VALUES (
                :payment_id, :subscription_id, :status, :amount, :currency,
                :failure_code, :failure_message, CAST(:metadata AS jsonb),
                CASE WHEN :status = 'paid' THEN now() ELSE NULL END
            )
            ON CONFLICT (provider, provider_payment_id) DO UPDATE SET
                provider_subscription_id = COALESCE(EXCLUDED.provider_subscription_id, billing_payments.provider_subscription_id),
                status = EXCLUDED.status,
                amount = EXCLUDED.amount,
                currency = EXCLUDED.currency,
                failure_code = EXCLUDED.failure_code,
                failure_message = EXCLUDED.failure_message,
                metadata = EXCLUDED.metadata,
                paid_at = COALESCE(EXCLUDED.paid_at, billing_payments.paid_at),
                updated_at = now()
            """),
            {
                "payment_id": payment_id,
                "subscription_id": subscription_id,
                "status": status,
                "amount": amount,
                "currency": currency,
                "failure_code": failure_code,
                "failure_message": failure_message,
                "metadata": json.dumps(metadata or {}),
            },
        )
    operation_id = None
    if metadata:
        operation_id = metadata.get("operation_id")

    await _reconcile_payment_operation_state(
        payment_id=payment_id,
        subscription_id=subscription_id,
        payment_status=status,
        failure_message=failure_message,
        operation_id=operation_id,
    )
    await append_billing_audit_log(
        user_id=None,
        subscription_id=subscription_id,
        operation_id=None,
        event_name=f"payment.{status}",
        payload={
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "failure_code": failure_code,
            "failure_message": failure_message,
            "metadata": metadata or {},
        },
    )


async def get_current_billing_operation(user_id: UUID, subscription_id: Optional[str]) -> Optional[dict]:
    """Return the newest relevant billing operation for UI visibility."""
    async with get_db_connection() as conn:
        query = """
            SELECT
                id::text,
                operation_type,
                status,
                ui_status,
                provider_subscription_id,
                requested_from_product_id,
                requested_to_product_id,
                result_product_id,
                failure_reason,
                metadata,
                started_at,
                completed_at
            FROM billing_operations
            WHERE user_id = :user_id
        """
        params: dict[str, Any] = {"user_id": user_id}
        if subscription_id is not None:
            query += """
              AND (
                provider_subscription_id = :subscription_id
                OR provider_subscription_id IS NULL
              )
            """
            params["subscription_id"] = subscription_id
        query += """
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = await conn.execute(text(query), params)
        row = result.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "type": row[1],
            "status": row[2],
            "ui_status": row[3],
            "subscription_id": row[4],
            "requested_from_product_id": row[5],
            "requested_to_product_id": row[6],
            "result_product_id": row[7],
            "failure_reason": row[8],
            "metadata": row[9] or {},
            "started_at": row[10].isoformat() if row[10] else None,
            "completed_at": row[11].isoformat() if row[11] else None,
        }


async def get_current_payment_issue(subscription_id: Optional[str]) -> Optional[dict]:
    """Return the latest actionable payment issue for the subscription."""
    if not subscription_id:
        return None

    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            SELECT
                provider_payment_id,
                status,
                amount,
                currency,
                failure_code,
                failure_message,
                updated_at
            FROM billing_payments
            WHERE provider_subscription_id = :subscription_id
              AND status IN ('failed', 'processing', 'requires_action')
            ORDER BY updated_at DESC
            LIMIT 1
            """),
            {"subscription_id": subscription_id},
        )
        row = result.fetchone()
        if not row:
            return None
        return {
            "payment_id": row[0],
            "status": row[1],
            "amount": row[2],
            "currency": row[3],
            "failure_code": row[4],
            "failure_message": row[5],
            "updated_at": row[6].isoformat() if row[6] else None,
        }


async def get_billing_history(
    user_id: UUID,
    subscription_id: Optional[str],
    limit: int = 20,
) -> list[dict]:
    """Return recent billing history for user visibility and supportability."""
    async with get_db_connection() as conn:
        query = """
            SELECT
                id::text,
                event_name,
                provider_subscription_id,
                operation_id::text,
                payload,
                created_at
            FROM billing_audit_log
            WHERE user_id = :user_id
        """
        params: dict[str, Any] = {"user_id": user_id, "limit": limit}
        if subscription_id is not None:
            query += """
               OR provider_subscription_id = :subscription_id
            """
            params["subscription_id"] = subscription_id
        query += """
            ORDER BY created_at DESC
            LIMIT :limit
        """
        result = await conn.execute(text(query), params)
        rows = result.fetchall()
    return [
        {
            "id": row[0],
            "event_name": row[1],
            "subscription_id": row[2],
            "operation_id": row[3],
            "payload": row[4] or {},
            "created_at": row[5].isoformat() if row[5] else None,
        }
        for row in rows
    ]


async def append_billing_audit_log(
    user_id: Optional[UUID],
    subscription_id: Optional[str],
    operation_id: Optional[str],
    event_name: str,
    payload: Optional[dict] = None,
) -> None:
    """Append a support/debug friendly billing timeline event."""
    resolved_user_id = user_id
    if resolved_user_id is None and subscription_id:
        resolved_user_id = await find_user_by_subscription_id(subscription_id)
    resolved_operation_id = UUID(operation_id) if operation_id else None

    async with get_db_connection() as conn:
        await conn.execute(
            text("""
            INSERT INTO billing_audit_log (
                user_id, provider_subscription_id, operation_id, event_name, payload
            )
            VALUES (
                :user_id, :subscription_id, :operation_id,
                :event_name, CAST(:payload AS jsonb)
            )
            """),
            {
                "user_id": resolved_user_id,
                "subscription_id": subscription_id,
                "operation_id": resolved_operation_id,
                "event_name": event_name,
                "payload": json.dumps(payload or {}),
            },
        )


async def _get_latest_pending_operation(
    conn,
    subscription_id: Optional[str],
    user_id: Optional[UUID],
    operation_type: str,
) -> Optional[dict]:
    query = """
        SELECT id::text, user_id, requested_from_product_id, requested_to_product_id, metadata
        FROM billing_operations
        WHERE operation_type = :operation_type
          AND status = 'pending'
    """
    params: dict[str, Any] = {"operation_type": operation_type}
    if subscription_id:
        query += " AND provider_subscription_id = :subscription_id"
        params["subscription_id"] = subscription_id
    elif user_id:
        query += " AND user_id = :user_id"
        params["user_id"] = user_id
    else:
        return None
    query += " ORDER BY created_at DESC LIMIT 1"
    result = await conn.execute(text(query), params)
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "user_id": row[1],
        "requested_from_product_id": row[2],
        "requested_to_product_id": row[3],
        "metadata": row[4] or {},
    }


async def _derive_subscription_fields(
    conn,
    subscription_id: str,
    incoming_product_id: str,
    status: str,
    cancel_at_period_end: bool,
    current_period_end: Optional[datetime],
) -> dict:
    normalized_status = (status or "").lower()
    now = datetime.now(timezone.utc)
    period_end = _parse_datetime(current_period_end)
    pending_upgrade = await _get_latest_pending_operation(
        conn=conn,
        subscription_id=subscription_id,
        user_id=None,
        operation_type=BillingOperationType.UPGRADE_REQUEST.value,
    )

    billing_state = BillingState.NONE.value
    if normalized_status == "active":
        billing_state = (
            BillingState.ACTIVE_CANCEL_SCHEDULED.value
            if cancel_at_period_end
            else BillingState.ACTIVE.value
        )
    elif normalized_status == "pending":
        billing_state = BillingState.PENDING_ACTIVATION.value
    elif normalized_status in {
        BillingState.ON_HOLD.value,
        BillingState.CANCELLED.value,
        BillingState.EXPIRED.value,
        BillingState.FAILED.value,
    }:
        billing_state = normalized_status

    effective_product_id = incoming_product_id
    pending_change_type = None
    pending_target_product_id = None
    pending_effective_at = None
    payment_status = PaymentStatus.NONE.value
    access_status = AccessStatus.NONE.value
    entitlement_status = EntitlementStatus.NONE.value
    last_payment_status = PaymentStatus.NONE.value
    last_paid_at = None

    if normalized_status == "active":
        payment_status = PaymentStatus.PAID.value
        access_status = AccessStatus.ACTIVE.value
        entitlement_status = EntitlementStatus.EFFECTIVE.value
        last_payment_status = PaymentStatus.PAID.value
        last_paid_at = now
    elif normalized_status == "pending":
        payment_status = PaymentStatus.PENDING.value
        access_status = AccessStatus.NONE.value
        entitlement_status = EntitlementStatus.PENDING_CHANGE.value
        last_payment_status = PaymentStatus.PENDING.value
    elif normalized_status == "on_hold":
        payment_status = PaymentStatus.FAILED.value
        last_payment_status = PaymentStatus.FAILED.value
        if pending_upgrade and pending_upgrade["requested_to_product_id"] == incoming_product_id:
            effective_product_id = pending_upgrade["requested_from_product_id"] or incoming_product_id
            pending_change_type = "upgrade"
            pending_target_product_id = pending_upgrade["requested_to_product_id"]
            pending_effective_at = period_end
        if await _has_prior_successful_paid_charge(conn, subscription_id):
            access_status = (
                AccessStatus.GRACE.value
                if period_end and period_end > now
                else AccessStatus.RESTRICTED.value
            )
            entitlement_status = (
                EntitlementStatus.EFFECTIVE.value
                if access_status == AccessStatus.GRACE.value
                else EntitlementStatus.ENDED.value
            )
        else:
            access_status = AccessStatus.ENDED.value
            entitlement_status = EntitlementStatus.ENDED.value
    elif normalized_status == "cancelled":
        payment_status = PaymentStatus.PAID.value
        last_payment_status = PaymentStatus.PAID.value
        access_status = (
            AccessStatus.GRACE.value
            if period_end and period_end > now
            else AccessStatus.ENDED.value
        )
        entitlement_status = (
            EntitlementStatus.EFFECTIVE.value
            if access_status == AccessStatus.GRACE.value
            else EntitlementStatus.ENDED.value
        )
        pending_change_type = "cancel" if cancel_at_period_end else None
        pending_effective_at = period_end if cancel_at_period_end else None
    elif normalized_status in {"expired", "failed"}:
        payment_status = PaymentStatus.FAILED.value if normalized_status == "failed" else PaymentStatus.CANCELLED.value
        last_payment_status = payment_status
        access_status = AccessStatus.ENDED.value
        entitlement_status = EntitlementStatus.ENDED.value

    return {
        "effective_product_id": effective_product_id,
        "billing_state": billing_state,
        "payment_status": payment_status,
        "access_status": access_status,
        "entitlement_status": entitlement_status,
        "pending_change_type": pending_change_type,
        "pending_target_product_id": pending_target_product_id,
        "pending_effective_at": pending_effective_at,
        "last_payment_status": last_payment_status,
        "last_paid_at": last_paid_at,
    }


async def _reconcile_operation_state(
    user_id: UUID,
    subscription_id: str,
    status: str,
    effective_product_id: str,
    current_product_id: str,
) -> None:
    normalized_status = (status or "").lower()
    async with get_db_connection() as conn:
        if normalized_status == "active":
            await conn.execute(
                text("""
                UPDATE billing_operations
                SET status = 'completed',
                    ui_status = 'completed',
                    result_product_id = COALESCE(:effective_product_id, result_product_id),
                    completed_at = COALESCE(completed_at, now()),
                    updated_at = now()
                WHERE user_id = :user_id
                  AND status = 'pending'
                  AND (
                    (operation_type = :checkout_start AND requested_to_product_id = :effective_product_id)
                    OR (operation_type = :upgrade_request AND requested_to_product_id = :current_product_id)
                  )
                """),
                {
                    "user_id": user_id,
                    "effective_product_id": effective_product_id,
                    "current_product_id": current_product_id,
                    "checkout_start": BillingOperationType.CHECKOUT_START.value,
                    "upgrade_request": BillingOperationType.UPGRADE_REQUEST.value,
                },
            )
        elif normalized_status in {"on_hold", "failed"}:
            await conn.execute(
                text("""
                UPDATE billing_operations
                SET status = 'failed',
                    ui_status = 'failed',
                    failure_reason = COALESCE(failure_reason, 'Billing operation failed during webhook reconciliation'),
                    updated_at = now()
                WHERE provider_subscription_id = :subscription_id
                  AND status = 'pending'
                  AND operation_type IN (:checkout_start, :upgrade_request, :reactivation_start)
                """).bindparams(
                    checkout_start=BillingOperationType.CHECKOUT_START.value,
                    upgrade_request=BillingOperationType.UPGRADE_REQUEST.value,
                    reactivation_start=BillingOperationType.REACTIVATION_START.value,
                ),
                {"subscription_id": subscription_id},
            )


async def _reconcile_payment_operation_state(
    payment_id: str,
    subscription_id: Optional[str],
    payment_status: str,
    failure_message: Optional[str],
    operation_id: Optional[str] = None,
) -> None:
    """Drive operation state from payment outcomes where possible."""
    async with get_db_connection() as conn:
        result = await conn.execute(
            text("""
            SELECT id::text, operation_type
            FROM billing_operations
            WHERE status = 'pending'
              AND (
                (
                    CAST(:operation_id AS uuid) IS NOT NULL
                    AND id = CAST(:operation_id AS uuid)
                )
                OR
                provider_subscription_id = :subscription_id
                OR COALESCE(metadata->>'payment_id', '') = :payment_id
              )
            ORDER BY created_at DESC
            LIMIT 1
            """),
            {
                "operation_id": operation_id,
                "subscription_id": subscription_id,
                "payment_id": payment_id,
            },
        )
        row = result.fetchone()
        if not row:
            return
        operation_id = row[0]
        operation_type = row[1]

        if payment_status == PaymentStatus.PAID.value:
            await conn.execute(
                text("""
                UPDATE billing_operations
                SET ui_status = 'completed',
                    updated_at = now()
                WHERE id = CAST(:operation_id AS uuid)
                """),
                {"operation_id": operation_id},
            )
        elif payment_status in {PaymentStatus.FAILED.value, PaymentStatus.CANCELLED.value}:
            if operation_type == BillingOperationType.UPGRADE_REQUEST.value and subscription_id:
                try:
                    recovery = await dodo_client.update_payment_method(
                        subscription_id=subscription_id,
                        return_url=get_settings().FRONTEND_RETURN_URL,
                    )
                except Exception as recovery_exc:
                    logger.warning(
                        "Failed to create payment recovery link for upgrade operation %s subscription %s: %s",
                        operation_id,
                        subscription_id,
                        recovery_exc,
                    )
                    recovery = None

                if recovery and recovery.get("payment_link"):
                    await conn.execute(
                        text("""
                        UPDATE billing_operations
                        SET status = 'pending',
                            ui_status = 'requires_action',
                            failure_reason = COALESCE(:failure_message, failure_reason, 'Payment failed'),
                            metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata_patch AS jsonb),
                            updated_at = now()
                        WHERE id = CAST(:operation_id AS uuid)
                        """),
                        {
                            "operation_id": operation_id,
                            "failure_message": failure_message,
                            "metadata_patch": json.dumps({
                                "payment_id": payment_id,
                                "payment_link": recovery.get("payment_link"),
                                "recovery_payment_id": recovery.get("payment_id"),
                            }),
                        },
                    )
                    return

            await conn.execute(
                text("""
                UPDATE billing_operations
                SET status = 'failed',
                    ui_status = 'failed',
                    failure_reason = COALESCE(:failure_message, failure_reason, 'Payment failed'),
                    updated_at = now()
                WHERE id = CAST(:operation_id AS uuid)
                """),
                {
                    "operation_id": operation_id,
                    "failure_message": failure_message,
                },
            )
