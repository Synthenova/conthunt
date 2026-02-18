# Telemetry Event Dictionary

This index lists key production events, their primary emitters, required properties, and an example payload shape.

## Search

### `search_started`
- Producer: `backend/app/api/v1/search.py`
- Required props: `search_id`, `platform_count`, `platforms`, `queue_duration_ms`, `source`
- Example:
```json
{
  "search_id": "uuid",
  "platform_count": 3,
  "platforms": ["youtube", "tiktok_keyword", "instagram_reels"],
  "queue_duration_ms": 42,
  "source": "backend_search_worker"
}
```

### `platform_search_completed`
- Producer: `backend/app/api/v1/search.py`
- Required props: `search_id`, `platform`, `success`, `duration_ms`, `result_count`, `http_status`, `error_category`, `source`

### `platform_load_more_completed`
- Producer: `backend/app/api/v1/search.py`
- Required props: `search_id`, `platform`, `success`, `duration_ms`, `result_count`, `http_status`, `error_category`, `source`

### `search_completed`
- Producer: `backend/app/api/v1/search.py`
- Required props: `search_id`, `success`, `duration_ms`, `total_duration_ms`, `queue_duration_ms`, `platform_count`, `result_count_total`, `source`
- Failure-only required props: `error_category`, `error_type`

### `search_no_results`
- Producer: `frontend/src/app/app/searches/[id]/page.tsx`
- Required props: `search_id`, `source`

### `search_result_clicked`
- Producer: `frontend/src/components/search/SelectableMediaCard.tsx`
- Required props: `search_id`, `platform`, `position`, `total_results`, `source`

## Boards

### `board_created`
- Producer: `frontend/src/app/app/boards/page.tsx`
- Required props: `board_id`, `source`

### `board_viewed`
- Producer: `frontend/src/app/app/boards/page.tsx`
- Required props: `board_id`, `item_count`, `source`

### `board_deleted`
- Producer: `frontend/src/app/app/boards/page.tsx`
- Required props: `board_id`, `item_count`, `source`

### `board_insights_completed` / `board_insights_failed`
- Producer: `backend/app/api/v1/tasks.py`
- Required props: `board_id`, `duration_ms`, `success`, `source`
- Failure-only required props: `error_category`, `error_type`

## Billing

### `pricing_page_viewed`
- Producer: `frontend/src/app/app/billing/return/PricingSection.tsx`
- Required props: `source`

### `pricing_plan_clicked`
- Producer: `frontend/src/app/app/billing/return/PricingSection.tsx`
- Required props: `product_id`, `plan_name`, `is_upgrade`, `source`

### `checkout_started` / `checkout_completed` / `checkout_failed`
- Producer: `frontend/src/app/app/billing/return/hooks/useBilling.ts`
- Required props: `product_id`, `source`
- `checkout_completed`: include `amount`, `currency`
- `checkout_failed`: include `reason`

### `subscription_renewed` / `subscription_cancelled`
- Producer: `backend/app/api/v1/webhooks_whop.py`
- Required props: `product_id`, `event_type`, `success`, `source`

### `payment_webhook_received` / `payment_confirmed` / `payment_webhook_failed`
- Producer: `backend/app/api/v1/webhooks.py`, `backend/app/services/telemetry_events.py`
- Required props: `event_type` (for webhook events), `source`, `success`
- Failure-only required props: `error_category`, `error_type`

## Canonical Lifecycle

### `action_started` / `action_succeeded` / `action_failed`
- Producers:
  - `frontend/src/features/telemetry/events.ts`
  - `backend/app/services/telemetry_events.py`
- Required props: `action_id`, `session_id`, `attempt_no`, `feature`, `operation`, `subject_type`, `subject_id`, `source`
- Failure-only required props: `error_kind`, `http_status`
