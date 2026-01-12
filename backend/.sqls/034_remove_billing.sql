-- Remove Dodo billing tables and columns
SET search_path = conthunt, public;
DROP TABLE IF EXISTS dodo_products CASCADE;
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS pending_plan_changes CASCADE;
DROP TABLE IF EXISTS webhook_events CASCADE;
DROP TABLE IF EXISTS plan_credits CASCADE;
DROP TABLE IF EXISTS feature_caps CASCADE;
DROP TABLE IF EXISTS dodo_webhook_events CASCADE; -- Just in case

ALTER TABLE users
  DROP COLUMN IF EXISTS dodo_customer_id,
  DROP COLUMN IF EXISTS dodo_subscription_id,
  DROP COLUMN IF EXISTS dodo_product_id,
  DROP COLUMN IF EXISTS dodo_status,
  DROP COLUMN IF EXISTS dodo_updated_at;
