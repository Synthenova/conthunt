"""Canonical billing domain enums shared by the hardening harness."""

from __future__ import annotations

from enum import StrEnum


class BillingState(StrEnum):
    NONE = "none"
    PENDING_ACTIVATION = "pending_activation"
    ACTIVE = "active"
    ACTIVE_CANCEL_SCHEDULED = "active_cancel_scheduled"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


class PaymentStatus(StrEnum):
    NONE = "none"
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    REQUIRES_ACTION = "requires_action"


class AccessStatus(StrEnum):
    NONE = "none"
    ACTIVE = "active"
    GRACE = "grace"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    ENDED = "ended"


class EntitlementStatus(StrEnum):
    NONE = "none"
    EFFECTIVE = "effective"
    PENDING_CHANGE = "pending_change"
    RESTRICTED = "restricted"
    ENDED = "ended"


class BillingOperationStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BillingOperationType(StrEnum):
    CHECKOUT_START = "checkout_start"
    CHECKOUT_COMPLETE = "checkout_complete"
    CHECKOUT_FAIL = "checkout_fail"
    UPGRADE_REQUEST = "upgrade_request"
    UPGRADE_APPLY = "upgrade_apply"
    UPGRADE_FAIL = "upgrade_fail"
    DOWNGRADE_SCHEDULE = "downgrade_schedule"
    DOWNGRADE_APPLY = "downgrade_apply"
    DOWNGRADE_CANCEL = "downgrade_cancel"
    CANCEL_SCHEDULE = "cancel_schedule"
    CANCEL_UNDO = "cancel_undo"
    REACTIVATION_START = "reactivation_start"
    REACTIVATION_COMPLETE = "reactivation_complete"
    REACTIVATION_FAIL = "reactivation_fail"
    SYNC_RECONCILE = "sync_reconcile"
