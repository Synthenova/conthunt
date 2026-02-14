# Telemetry Contract

This project uses a feature-agnostic telemetry contract. Chat is the first fully instrumented feature.

## Required Fields (when available)

- `action_id`: New UUID for each user action attempt.
- `session_id`: Stable browser/session identifier.
- `attempt_no`: 1-based attempt count for retries of the same logical action.
- `user_id`: Authenticated user identifier.
- `feature`: Product surface, for example `chat`, `search`, `billing`.
- `operation`: Action verb, for example `send_message`, `stream_response`, `checkout`.
- `subject_type`: Domain object type, for example `chat_message`, `search_job`, `subscription`.
- `subject_id`: Domain object identifier.

## Optional Fields

- `outcome`: `started`, `succeeded`, `failed`.
- `duration_ms`
- `error_kind`
- `http_status`
- `metadata`: Structured, redacted payload.

## Header Contract

Frontend sends these headers to backend endpoints for correlation propagation:

- `x-session-id`
- `x-action-id`
- `x-attempt-no`
- `x-feature`
- `x-operation`
- `x-subject-type`
- `x-subject-id`

Migration header kept for chat compatibility:

- `x-message-client-id`

When `x-subject-id` is missing and `x-message-client-id` exists, backend maps it to `subject_id`.

## Canonical Events

Canonical lifecycle events:

- `action_started`
- `action_succeeded`
- `action_failed`

Feature semantic events are optional aliases. Chat currently emits both canonical and semantic events.

## Chat Mapping

- Send message:
  - `feature=chat`
  - `operation=send_message`
  - `subject_type=chat_message`
  - `subject_id=<message_client_id>`
- Stream response:
  - `feature=chat`
  - `operation=stream_response`
  - `subject_type=chat_message`
  - `subject_id=<message_client_id>`

Retry semantics:

- Keep `subject_id` stable for the same logical message.
- Generate a new `action_id` for each retry.
- Increment `attempt_no` for each retry.

## Backend Span Attributes

The middleware and runtime helpers add telemetry to OpenTelemetry spans:

- `action.id`
- `session.id`
- `enduser.id`
- `app.feature`
- `app.operation`
- `app.subject_type`
- `app.subject_id`
- `app.attempt_no`
- `chat.message_client_id` (chat compatibility)
- `task.retry_count` (Cloud Tasks retries)

## Redaction Rules

Data sent to PostHog/Langfuse must be redacted before emission.

Redact keys matching:

- `token`, `secret`, `password`, `authorization`, `cookie`, `api_key`, `webhook_signature`

Also redact Bearer-like strings and long credential-looking values.
