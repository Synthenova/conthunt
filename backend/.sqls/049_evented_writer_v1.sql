-- V1 centralized evented write backbone (minimal complexity)

CREATE TABLE IF NOT EXISTS conthunt.write_outbox (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    domain text NOT NULL,
    event_type text NOT NULL,
    ordering_mode text NOT NULL CHECK (ordering_mode IN ('strict', 'unordered')),
    partition_key text NOT NULL,
    idempotency_key text NOT NULL,
    actor_user_id uuid,
    actor_role text,
    source text,
    payload jsonb NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'done', 'retry', 'dead')),
    attempt_count integer NOT NULL DEFAULT 0,
    next_attempt_at timestamptz NOT NULL DEFAULT now(),
    leased_by text,
    lease_until timestamptz,
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT write_outbox_domain_idempotency_unique UNIQUE (domain, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_outbox_sched
    ON conthunt.write_outbox (status, next_attempt_at, created_at);

CREATE INDEX IF NOT EXISTS idx_outbox_strict_partition
    ON conthunt.write_outbox (partition_key, status, next_attempt_at, created_at)
    WHERE ordering_mode = 'strict';

CREATE INDEX IF NOT EXISTS idx_outbox_lease_expiry
    ON conthunt.write_outbox (lease_until);


CREATE TABLE IF NOT EXISTS conthunt.processed_events (
    handler_name text NOT NULL,
    event_id uuid NOT NULL,
    idempotency_key text NOT NULL,
    processed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (handler_name, event_id)
);

CREATE INDEX IF NOT EXISTS idx_processed_by_key
    ON conthunt.processed_events (handler_name, idempotency_key);
