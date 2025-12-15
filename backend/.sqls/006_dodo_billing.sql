SET search_path = conthunt, public;

ALTER TABLE conthunt.users
ADD COLUMN IF NOT EXISTS dodo_customer_id text,
ADD COLUMN IF NOT EXISTS dodo_subscription_id text,
ADD COLUMN IF NOT EXISTS dodo_product_id text,
ADD COLUMN IF NOT EXISTS dodo_status text,
ADD COLUMN IF NOT EXISTS dodo_updated_at timestamptz DEFAULT now();

-- Optional: Idempotency table for webhooks
CREATE TABLE IF NOT EXISTS conthunt.dodo_webhook_events (
  webhook_id text PRIMARY KEY,
  received_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_dodo_subscription_id ON conthunt.users(dodo_subscription_id);
