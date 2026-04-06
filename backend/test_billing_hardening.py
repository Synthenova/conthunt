from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("SCRAPECREATORS_API_KEY", "test")

from app.auth import get_current_user
from app.api.v1 import billing as billing_api
from app.api.v1 import webhooks as billing_webhooks
from app.billing.domain import AccessStatus, EntitlementStatus, PaymentStatus
from app.services import billing_service


class _FakeResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows if rows is not None else ([] if row is None else [row])

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _FakeConn:
    def __init__(self, row=None):
        self._row = row

    async def execute(self, *args, **kwargs):
        return _FakeResult(self._row)


class _FakeConnWithExecuteCalls:
    def __init__(self, row=None, results=None):
        self._row = row
        self._results = list(results or [])
        self.calls = []

    async def execute(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self._results:
            next_result = self._results.pop(0)
            if isinstance(next_result, _FakeResult):
                return next_result
            if isinstance(next_result, dict):
                return _FakeResult(row=next_result.get("row"), rows=next_result.get("rows"))
            return _FakeResult(row=next_result)
        return _FakeResult(self._row)


class _FakeDbContext:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _build_test_app(router, dependency_overrides=None):
    app = FastAPI()
    app.include_router(router)
    for dependency, override in (dependency_overrides or {}).items():
        app.dependency_overrides[dependency] = override
    return app


@pytest.mark.asyncio
async def test_derive_subscription_fields_keeps_old_entitlements_for_failed_upgrade():
    future_end = datetime.now(timezone.utc) + timedelta(days=7)
    pending_upgrade_row = (
        "op-1",
        "user-1",
        "prod_creator_monthly",
        "prod_pro_monthly",
        {},
    )

    derived = await billing_service._derive_subscription_fields(
        conn=_FakeConn(row=pending_upgrade_row),
        subscription_id="sub_123",
        incoming_product_id="prod_pro_monthly",
        status="on_hold",
        cancel_at_period_end=False,
        current_period_end=future_end,
    )

    assert derived["effective_product_id"] == "prod_creator_monthly"
    assert derived["payment_status"] == PaymentStatus.FAILED.value
    assert derived["access_status"] == AccessStatus.GRACE.value
    assert derived["entitlement_status"] == EntitlementStatus.EFFECTIVE.value
    assert derived["pending_change_type"] == "upgrade"
    assert derived["pending_target_product_id"] == "prod_pro_monthly"


@pytest.mark.asyncio
async def test_derive_subscription_fields_for_active_subscription_marks_paid_access():
    derived = await billing_service._derive_subscription_fields(
        conn=_FakeConn(row=None),
        subscription_id="sub_123",
        incoming_product_id="prod_creator_monthly",
        status="active",
        cancel_at_period_end=False,
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )

    assert derived["effective_product_id"] == "prod_creator_monthly"
    assert derived["payment_status"] == PaymentStatus.PAID.value
    assert derived["access_status"] == AccessStatus.ACTIVE.value
    assert derived["entitlement_status"] == EntitlementStatus.EFFECTIVE.value


@pytest.mark.asyncio
async def test_get_billing_context_includes_snapshot_operation_issue_and_history(monkeypatch):
    monkeypatch.setattr(
        billing_service,
        "get_user_subscription",
        AsyncMock(
            return_value={
                "subscription_id": "sub_123",
                "product_id": "prod_creator_monthly",
                "provider_product_id": "prod_pro_monthly",
                "effective_product_id": "prod_creator_monthly",
                "status": "on_hold",
                "billing_state": "on_hold",
                "payment_status": "failed",
                "access_status": "grace",
                "entitlement_status": "effective",
                "cancel_at_period_end": False,
                "current_period_start": "2026-03-01T00:00:00+00:00",
                "current_period_end": "2026-04-01T00:00:00+00:00",
                "pending_change_type": "upgrade",
                "pending_target_product_id": "prod_pro_monthly",
                "pending_effective_at": "2026-04-01T00:00:00+00:00",
                "db_role": "creator",
            }
        ),
    )
    monkeypatch.setattr(
        billing_service,
        "get_current_billing_operation",
        AsyncMock(return_value={"id": "op_1", "type": "upgrade_request", "status": "failed"}),
    )
    monkeypatch.setattr(
        billing_service,
        "get_current_payment_issue",
        AsyncMock(return_value={"payment_id": "pay_1", "status": "failed", "failure_message": "Card declined"}),
    )
    monkeypatch.setattr(
        billing_service,
        "get_billing_history",
        AsyncMock(return_value=[{"id": "evt_1", "event_name": "payment.failed"}]),
    )
    monkeypatch.setattr(
        billing_service,
        "get_trial_summary",
        AsyncMock(
            return_value={
                "is_trialing": True,
                "trial_ends_at": "2026-04-08T00:00:00+00:00",
                "first_charge_at": "2026-04-08T00:00:00+00:00",
                "trial_period_days": 7,
            }
        ),
    )

    context = await billing_service.get_billing_context(user_id="user-1")

    assert context["role"] == "creator"
    assert context["billing_state"] == "on_hold"
    assert context["access_granted"] is True
    assert context["summary"]["effective_product_id"] == "prod_creator_monthly"
    assert context["summary"]["provider_product_id"] == "prod_pro_monthly"
    assert context["pending_change"]["type"] == "upgrade"
    assert context["current_operation"]["id"] == "op_1"
    assert context["payment_issue"]["payment_id"] == "pay_1"
    assert context["history"][0]["event_name"] == "payment.failed"
    assert context["summary"]["is_trialing"] is True
    assert context["summary"]["trial_period_days"] == 7


@pytest.mark.asyncio
async def test_create_checkout_is_gated_and_returns_operation_id(monkeypatch):
    monkeypatch.setattr(
        billing_service,
        "require_allowed_action",
        AsyncMock(return_value={"billing_state": "none"}),
    )
    monkeypatch.setattr(
        billing_service,
        "create_billing_operation",
        AsyncMock(return_value="op_123"),
    )
    monkeypatch.setattr(
        billing_service,
        "attach_operation_external_refs",
        AsyncMock(),
    )
    checkout_mock = AsyncMock(return_value={"session_id": "cs_123", "url": "https://checkout.test"})
    monkeypatch.setattr(billing_service.dodo_client, "create_checkout_session", checkout_mock)
    monkeypatch.setattr(billing_service, "capture_event", lambda *args, **kwargs: None)

    result = await billing_service.create_checkout(
        user_id="user-1",
        email="test@example.com",
        product_id="prod_creator_monthly",
        dodo_customer_id=None,
    )

    assert result["operation_id"] == "op_123"
    checkout_mock.assert_awaited_once()
    kwargs = checkout_mock.await_args.kwargs
    assert kwargs["metadata"]["user_id"] == "user-1"
    assert kwargs["metadata"]["operation_id"] == "op_123"


@pytest.mark.asyncio
async def test_create_checkout_marks_operation_failed_when_checkout_creation_errors(monkeypatch):
    monkeypatch.setattr(
        billing_service,
        "require_allowed_action",
        AsyncMock(return_value={"billing_state": "none"}),
    )
    monkeypatch.setattr(
        billing_service,
        "create_billing_operation",
        AsyncMock(return_value="op_123"),
    )
    mark_failed_mock = AsyncMock()
    monkeypatch.setattr(billing_service, "mark_billing_operation_failed", mark_failed_mock)
    monkeypatch.setattr(
        billing_service.dodo_client,
        "create_checkout_session",
        AsyncMock(side_effect=RuntimeError("boom")),
    )

    with pytest.raises(RuntimeError, match="boom"):
        await billing_service.create_checkout(
            user_id="user-1",
            email="test@example.com",
            product_id="prod_creator_monthly",
            dodo_customer_id=None,
        )

    mark_failed_mock.assert_awaited_once_with("op_123", "boom")


@pytest.mark.asyncio
async def test_billing_history_route_returns_history(monkeypatch):
    monkeypatch.setattr(
        billing_api.billing_service,
        "get_billing_context",
        AsyncMock(return_value={"subscription_id": "sub_123"}),
    )
    monkeypatch.setattr(
        billing_api.billing_service,
        "get_billing_history",
        AsyncMock(return_value=[{"id": "evt_1", "event_name": "subscription.active"}]),
    )

    user = {"db_user_id": "user-1"}
    result = await billing_api.get_billing_history(user)

    assert result == {"history": [{"id": "evt_1", "event_name": "subscription.active"}]}


@pytest.mark.asyncio
async def test_append_billing_audit_log_binds_uuid_operation_id(monkeypatch):
    fake_conn = _FakeConnWithExecuteCalls()
    monkeypatch.setattr(billing_service, "get_db_connection", lambda: _FakeDbContext(fake_conn))

    await billing_service.append_billing_audit_log(
        user_id="user-1",
        subscription_id=None,
        operation_id="5d3c71ee-4f73-4f59-9c2b-28c2f0960479",
        event_name="operation.checkout_start",
        payload={"ok": True},
    )

    params = fake_conn.calls[0][0][1]
    assert str(params["operation_id"]) == "5d3c71ee-4f73-4f59-9c2b-28c2f0960479"


@pytest.mark.asyncio
async def test_record_payment_event_reconciles_by_operation_id_from_metadata(monkeypatch):
    fake_conn = _FakeConnWithExecuteCalls()
    reconcile_mock = AsyncMock()
    audit_mock = AsyncMock()

    monkeypatch.setattr(billing_service, "get_db_connection", lambda: _FakeDbContext(fake_conn))
    monkeypatch.setattr(billing_service, "_reconcile_payment_operation_state", reconcile_mock)
    monkeypatch.setattr(billing_service, "append_billing_audit_log", audit_mock)

    await billing_service.record_payment_event(
        payment_id="pay_123",
        subscription_id=None,
        status="failed",
        amount=1999,
        currency="USD",
        failure_message="Card declined",
        metadata={"operation_id": "op_123", "source": "checkout"},
    )

    reconcile_mock.assert_awaited_once_with(
        payment_id="pay_123",
        subscription_id=None,
        payment_status="failed",
        failure_message="Card declined",
        operation_id="op_123",
    )
    assert fake_conn.calls


@pytest.mark.asyncio
async def test_handle_payment_failed_preserves_webhook_metadata_for_operation_reconciliation(monkeypatch):
    record_payment_mock = AsyncMock()
    monkeypatch.setattr(billing_webhooks.billing_service, "record_payment_event", record_payment_mock)

    data = SimpleNamespace(
        payment_id="pay_123",
        subscription_id=None,
        total_amount=1999,
        currency="USD",
        failure_code="card_declined",
        error_message="Card declined",
        payload_type="Payment",
        metadata={"operation_id": "op_123", "user_id": "user-1"},
    )

    await billing_webhooks.handle_payment_failed(data)

    record_payment_mock.assert_awaited_once()
    kwargs = record_payment_mock.await_args.kwargs
    assert kwargs["metadata"]["operation_id"] == "op_123"
    assert kwargs["metadata"]["user_id"] == "user-1"
    assert kwargs["metadata"]["payload_type"] == "Payment"


@pytest.mark.asyncio
async def test_request_cancel_cancels_pending_downgrade_and_records_operation(monkeypatch):
    monkeypatch.setattr(
        billing_service,
        "require_allowed_action",
        AsyncMock(
            return_value={
                "subscription_id": "sub_123",
                "product_id": "prod_creator_monthly",
                "current_period_end": "2026-04-01T00:00:00+00:00",
            }
        ),
    )
    cancel_pending_mock = AsyncMock(return_value=True)
    create_operation_mock = AsyncMock(return_value="op_cancel")
    set_cancel_mock = AsyncMock()

    monkeypatch.setattr(billing_service, "cancel_pending_downgrade", cancel_pending_mock)
    monkeypatch.setattr(billing_service, "create_billing_operation", create_operation_mock)
    monkeypatch.setattr(billing_service.dodo_client, "set_cancel_at_period_end", set_cancel_mock)

    result = await billing_service.request_cancel("user-1")

    cancel_pending_mock.assert_awaited_once_with("user-1", record_operation=False)
    set_cancel_mock.assert_awaited_once_with(subscription_id="sub_123", cancel=True)
    create_operation_mock.assert_awaited_once()
    kwargs = create_operation_mock.await_args.kwargs
    assert kwargs["operation_type"] == billing_service.BillingOperationType.CANCEL_SCHEDULE.value
    assert result["access_until"] == "2026-04-01T00:00:00+00:00"


@pytest.mark.asyncio
async def test_undo_cancel_clears_cancel_at_period_end_and_records_operation(monkeypatch):
    monkeypatch.setattr(
        billing_service,
        "require_allowed_action",
        AsyncMock(
            return_value={
                "subscription_id": "sub_123",
                "product_id": "prod_creator_monthly",
            }
        ),
    )
    create_operation_mock = AsyncMock(return_value="op_undo")
    set_cancel_mock = AsyncMock()

    monkeypatch.setattr(billing_service, "create_billing_operation", create_operation_mock)
    monkeypatch.setattr(billing_service.dodo_client, "set_cancel_at_period_end", set_cancel_mock)

    result = await billing_service.undo_cancel("user-1")

    set_cancel_mock.assert_awaited_once_with(subscription_id="sub_123", cancel=False)
    create_operation_mock.assert_awaited_once()
    kwargs = create_operation_mock.await_args.kwargs
    assert kwargs["operation_type"] == billing_service.BillingOperationType.CANCEL_UNDO.value
    assert result == {"message": "Subscription cancellation has been undone"}


@pytest.mark.asyncio
async def test_classify_plan_change_marks_cross_interval_higher_tier_as_upgrade(monkeypatch):
    products = [
        {
            "product_id": "prod_creator_monthly",
            "name": "Creator Monthly",
            "price": 2900,
            "currency": "USD",
            "metadata": {"app_role": "creator", "credits": "1000"},
        },
        {
            "product_id": "prod_creator_annual",
            "name": "Creator Annual",
            "price": 30000,
            "currency": "USD",
            "metadata": {"app_role": "creator", "credits": "1000"},
        },
        {
            "product_id": "prod_pro_monthly",
            "name": "Research Monthly",
            "price": 7900,
            "currency": "USD",
            "metadata": {"app_role": "pro_research", "credits": "3000"},
        },
        {
            "product_id": "prod_pro_annual",
            "name": "Research Annual",
            "price": 75600,
            "currency": "USD",
            "metadata": {"app_role": "pro_research", "credits": "3000"},
        },
    ]

    classification = await billing_service.classify_plan_change(
        current_product_id="prod_creator_annual",
        target_product_id="prod_pro_monthly",
        products=products,
    )

    assert classification["transition_type"] == "upgrade"
    assert classification["cross_interval"] is True
    assert classification["proration_mode"] == "prorated_immediately"
    assert classification["on_payment_failure"] == "prevent_change"


@pytest.mark.asyncio
async def test_get_trial_summary_infers_trial_window(monkeypatch):
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(days=2)
    next_billing_date = now + timedelta(days=5)
    monkeypatch.setattr(
        billing_service.dodo_client,
        "get_subscription",
        AsyncMock(
            return_value={
                "subscription_id": "sub_123",
                "status": "active",
                "created_at": created_at,
                "trial_period_days": 7,
                "next_billing_date": next_billing_date,
            }
        ),
    )

    summary = await billing_service.get_trial_summary("sub_123")

    assert summary["is_trialing"] is True
    assert summary["trial_period_days"] == 7
    assert summary["trial_ends_at"] is not None
    assert summary["first_charge_at"] == summary["trial_ends_at"]


@pytest.mark.asyncio
async def test_request_downgrade_schedules_provider_change(monkeypatch):
    context = {
        "subscription_id": "sub_123",
        "product_id": "prod_pro_annual",
        "current_period_end": "2026-05-01T00:00:00+00:00",
    }
    products = [
        {
            "product_id": "prod_creator_monthly",
            "name": "Creator Monthly",
            "price": 2900,
            "currency": "USD",
            "metadata": {"app_role": "creator", "credits": "1000"},
        },
        {
            "product_id": "prod_creator_annual",
            "name": "Creator Annual",
            "price": 30000,
            "currency": "USD",
            "metadata": {"app_role": "creator", "credits": "1000"},
        },
        {
            "product_id": "prod_pro_monthly",
            "name": "Research Monthly",
            "price": 7900,
            "currency": "USD",
            "metadata": {"app_role": "pro_research", "credits": "3000"},
        },
        {
            "product_id": "prod_pro_annual",
            "name": "Research Annual",
            "price": 75600,
            "currency": "USD",
            "metadata": {"app_role": "pro_research", "credits": "3000"},
        },
    ]
    schedule_mock = AsyncMock()
    set_pending_mock = AsyncMock()
    create_operation_mock = AsyncMock()
    cancel_pending_mock = AsyncMock(return_value=False)

    monkeypatch.setattr(billing_service, "require_allowed_action", AsyncMock(return_value=context))
    monkeypatch.setattr(billing_service.dodo_client, "get_products", AsyncMock(return_value=products))
    monkeypatch.setattr(billing_service.dodo_client, "schedule_plan_change", schedule_mock)
    monkeypatch.setattr(billing_service, "_set_subscription_pending_change", set_pending_mock)
    monkeypatch.setattr(billing_service, "create_billing_operation", create_operation_mock)
    monkeypatch.setattr(billing_service, "cancel_pending_downgrade", cancel_pending_mock)

    result = await billing_service.request_downgrade("user-1", "prod_creator_monthly")

    schedule_mock.assert_awaited_once_with(
        subscription_id="sub_123",
        product_id="prod_creator_monthly",
        metadata={"scheduled_by": "backend_billing_downgrade"},
    )
    set_pending_mock.assert_awaited_once()
    create_operation_mock.assert_awaited_once()
    assert result["target_role"] == "creator"
    assert result["effective_at"] == context["current_period_end"]


@pytest.mark.asyncio
async def test_handle_subscription_renewed_only_syncs_state(monkeypatch):
    apply_state_mock = AsyncMock()

    monkeypatch.setattr(billing_webhooks.billing_service, "find_user_by_subscription_id", AsyncMock(return_value="user-1"))
    monkeypatch.setattr(billing_webhooks.billing_service, "find_user_by_customer_id", AsyncMock(return_value=None))
    monkeypatch.setattr(billing_webhooks.billing_service, "find_user_by_metadata", AsyncMock(return_value=None))
    monkeypatch.setattr(billing_webhooks.billing_service, "apply_subscription_state", apply_state_mock)

    event_ts = datetime.now(timezone.utc)
    data = SimpleNamespace(
        subscription_id="sub_123",
        customer=SimpleNamespace(customer_id="cust_123"),
        metadata={"user_id": "user-1"},
        product_id="prod_pro_monthly",
        cancel_at_next_billing_date=False,
        previous_billing_date=event_ts - timedelta(days=30),
        next_billing_date=event_ts + timedelta(days=30),
    )

    await billing_webhooks.handle_subscription_renewed(data, event_ts)

    apply_state_mock.assert_awaited_once()
    kwargs = apply_state_mock.await_args.kwargs
    assert kwargs["user_id"] == "user-1"
    assert kwargs["status"] == "active"


@pytest.mark.asyncio
async def test_handle_subscription_on_hold_uses_customer_lookup_and_applies_state(monkeypatch):
    apply_state_mock = AsyncMock()
    monkeypatch.setattr(billing_webhooks.billing_service, "find_user_by_subscription_id", AsyncMock(return_value=None))
    monkeypatch.setattr(billing_webhooks.billing_service, "find_user_by_customer_id", AsyncMock(return_value="user-1"))
    monkeypatch.setattr(billing_webhooks.billing_service, "find_user_by_metadata", AsyncMock(return_value=None))
    monkeypatch.setattr(billing_webhooks.billing_service, "apply_subscription_state", apply_state_mock)

    event_ts = datetime.now(timezone.utc)
    data = SimpleNamespace(
        subscription_id="sub_123",
        customer=SimpleNamespace(customer_id="cust_123"),
        metadata={},
        product_id="prod_pro_monthly",
        cancel_at_next_billing_date=False,
        previous_billing_date=event_ts - timedelta(days=15),
        next_billing_date=event_ts + timedelta(days=15),
    )

    await billing_webhooks.handle_subscription_on_hold(data, event_ts)

    apply_state_mock.assert_awaited_once()
    kwargs = apply_state_mock.await_args.kwargs
    assert kwargs["user_id"] == "user-1"
    assert kwargs["status"] == "on_hold"
    assert kwargs["subscription_id"] == "sub_123"


@pytest.mark.asyncio
async def test_apply_subscription_state_ignores_stale_webhook_without_side_effects(monkeypatch):
    fake_conn = _FakeConnWithExecuteCalls(
        results=[
            {"row": None},
            {"row": None},
        ]
    )
    sync_role_mock = AsyncMock()
    reconcile_operation_mock = AsyncMock()
    audit_mock = AsyncMock()
    derive_mock = AsyncMock(
        return_value={
            "effective_product_id": "prod_creator_monthly",
            "billing_state": "active",
            "payment_status": "paid",
            "access_status": "active",
            "entitlement_status": "effective",
            "pending_change_type": None,
            "pending_target_product_id": None,
            "pending_effective_at": None,
            "last_payment_status": "paid",
            "last_paid_at": datetime.now(timezone.utc),
        }
    )

    monkeypatch.setattr(billing_service, "get_db_connection", lambda: _FakeDbContext(fake_conn))
    monkeypatch.setattr(billing_service, "_derive_subscription_fields", derive_mock)
    monkeypatch.setattr(billing_service, "_sync_firebase_role", sync_role_mock)
    monkeypatch.setattr(billing_service, "_reconcile_operation_state", reconcile_operation_mock)
    monkeypatch.setattr(billing_service, "append_billing_audit_log", audit_mock)

    await billing_service.apply_subscription_state(
        user_id="user-1",
        subscription_id="sub_123",
        customer_id="cust_123",
        product_id="prod_creator_monthly",
        status="active",
        cancel_at_period_end=False,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=29),
        webhook_ts=datetime.now(timezone.utc) - timedelta(days=10),
    )

    assert len(fake_conn.calls) == 2
    sync_role_mock.assert_not_awaited()
    reconcile_operation_mock.assert_not_awaited()
    audit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_reconcile_payment_success_sets_ui_completed_only(monkeypatch):
    fake_conn = _FakeConnWithExecuteCalls(
        results=[
            {"row": ("op_123",)},
            {"row": None},
        ]
    )
    monkeypatch.setattr(billing_service, "get_db_connection", lambda: _FakeDbContext(fake_conn))

    await billing_service._reconcile_payment_operation_state(
        payment_id="pay_123",
        subscription_id="sub_123",
        payment_status=PaymentStatus.PAID.value,
        failure_message=None,
        operation_id="op_123",
    )

    assert len(fake_conn.calls) == 2
    update_sql = str(fake_conn.calls[1][0][0])
    assert "SET ui_status = 'completed'" in update_sql
    assert "SET status = 'completed'" not in update_sql


@pytest.mark.asyncio
async def test_reconcile_operation_active_completes_pending_upgrade(monkeypatch):
    fake_conn = _FakeConnWithExecuteCalls(results=[{"row": None}])
    monkeypatch.setattr(billing_service, "get_db_connection", lambda: _FakeDbContext(fake_conn))

    await billing_service._reconcile_operation_state(
        user_id="user-1",
        subscription_id="sub_123",
        status="active",
        effective_product_id="prod_pro_monthly",
        current_product_id="prod_pro_monthly",
    )

    assert len(fake_conn.calls) == 1
    update_sql = str(fake_conn.calls[0][0][0])
    assert "SET status = 'completed'" in update_sql
    assert "operation_type = :upgrade_request" in update_sql


def test_webhook_route_returns_already_processed_for_duplicate_event(monkeypatch):
    event = SimpleNamespace(
        type="subscription.active",
        data=SimpleNamespace(
            subscription_id="sub_123",
            customer=SimpleNamespace(customer_id="cust_123"),
            product_id="prod_creator_monthly",
            metadata={"user_id": "user-1"},
            cancel_at_next_billing_date=False,
            previous_billing_date=datetime.now(timezone.utc) - timedelta(days=1),
            next_billing_date=datetime.now(timezone.utc) + timedelta(days=29),
        ),
        timestamp=datetime.now(timezone.utc),
    )
    unwrap_client = SimpleNamespace(webhooks=SimpleNamespace(unwrap=lambda body, headers: event))
    active_mock = AsyncMock()

    monkeypatch.setattr(billing_webhooks.dodo_client, "get_dodo_client", lambda: unwrap_client)
    monkeypatch.setattr(billing_webhooks.billing_service, "record_webhook_inbox_event", AsyncMock(return_value=False))
    monkeypatch.setattr(billing_webhooks, "handle_subscription_active", active_mock)

    app = _build_test_app(billing_webhooks.router)
    with TestClient(app) as client:
        response = client.post(
            "/webhooks/dodo",
            content=b'{"type":"subscription.active"}',
            headers={
                "webhook-id": "wh_123",
                "webhook-signature": "sig",
                "webhook-timestamp": "123",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"status": "already_processed"}
    active_mock.assert_not_awaited()


def test_webhook_route_marks_processed_for_successful_event(monkeypatch):
    event = SimpleNamespace(
        type="subscription.active",
        data=SimpleNamespace(
            subscription_id="sub_123",
            customer=SimpleNamespace(customer_id="cust_123"),
            product_id="prod_creator_monthly",
            metadata={"user_id": "user-1"},
            cancel_at_next_billing_date=False,
            previous_billing_date=datetime.now(timezone.utc) - timedelta(days=1),
            next_billing_date=datetime.now(timezone.utc) + timedelta(days=29),
        ),
        timestamp=datetime.now(timezone.utc),
    )
    unwrap_client = SimpleNamespace(webhooks=SimpleNamespace(unwrap=lambda body, headers: event))
    active_mock = AsyncMock()
    mark_status_mock = AsyncMock()

    monkeypatch.setattr(billing_webhooks.dodo_client, "get_dodo_client", lambda: unwrap_client)
    monkeypatch.setattr(billing_webhooks.billing_service, "record_webhook_inbox_event", AsyncMock(return_value=True))
    monkeypatch.setattr(billing_webhooks.billing_service, "mark_webhook_inbox_status", mark_status_mock)
    monkeypatch.setattr(billing_webhooks, "handle_subscription_active", active_mock)

    app = _build_test_app(billing_webhooks.router)
    with TestClient(app) as client:
        response = client.post(
            "/webhooks/dodo",
            content=b'{"type":"subscription.active"}',
            headers={
                "webhook-id": "wh_123",
                "webhook-signature": "sig",
                "webhook-timestamp": "123",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    active_mock.assert_awaited_once()
    mark_status_mock.assert_awaited_once_with("wh_123", "processed")


def test_webhook_route_marks_failed_and_returns_500_on_handler_error(monkeypatch):
    event = SimpleNamespace(
        type="subscription.active",
        data=SimpleNamespace(
            subscription_id="sub_123",
            customer=SimpleNamespace(customer_id="cust_123"),
            product_id="prod_creator_monthly",
            metadata={"user_id": "user-1"},
            cancel_at_next_billing_date=False,
            previous_billing_date=datetime.now(timezone.utc) - timedelta(days=1),
            next_billing_date=datetime.now(timezone.utc) + timedelta(days=29),
        ),
        timestamp=datetime.now(timezone.utc),
    )
    unwrap_client = SimpleNamespace(webhooks=SimpleNamespace(unwrap=lambda body, headers: event))
    mark_status_mock = AsyncMock()

    monkeypatch.setattr(billing_webhooks.dodo_client, "get_dodo_client", lambda: unwrap_client)
    monkeypatch.setattr(billing_webhooks.billing_service, "record_webhook_inbox_event", AsyncMock(return_value=True))
    monkeypatch.setattr(billing_webhooks.billing_service, "mark_webhook_inbox_status", mark_status_mock)
    monkeypatch.setattr(billing_webhooks, "handle_subscription_active", AsyncMock(side_effect=RuntimeError("boom")))
    monkeypatch.setattr(billing_webhooks, "capture_event_with_error", lambda *args, **kwargs: None)

    app = _build_test_app(billing_webhooks.router)
    with TestClient(app) as client:
        response = client.post(
            "/webhooks/dodo",
            content=b'{"type":"subscription.active"}',
            headers={
                "webhook-id": "wh_123",
                "webhook-signature": "sig",
                "webhook-timestamp": "123",
            },
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Webhook processing failed"
    mark_status_mock.assert_awaited_once_with("wh_123", "failed", "boom")


def test_billing_history_route_via_http_uses_auth_override(monkeypatch):
    monkeypatch.setattr(
        billing_api.billing_service,
        "get_billing_context",
        AsyncMock(return_value={"subscription_id": "sub_123"}),
    )
    monkeypatch.setattr(
        billing_api.billing_service,
        "get_billing_history",
        AsyncMock(return_value=[{"id": "evt_1", "event_name": "subscription.active"}]),
    )

    app = _build_test_app(
        billing_api.router,
        dependency_overrides={get_current_user: lambda: {"db_user_id": "user-1", "email": "test@example.com"}},
    )
    with TestClient(app) as client:
        response = client.get("/billing/history")

    assert response.status_code == 200
    assert response.json() == {"history": [{"id": "evt_1", "event_name": "subscription.active"}]}
