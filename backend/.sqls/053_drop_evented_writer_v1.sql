-- Drop the v1 evented writer/outbox tables.
-- Safe to run multiple times.
--
-- This removes:
-- - write_outbox: queued write events
-- - processed_events: idempotency markers for write worker
--
-- If you still have application code referencing these tables, run this only
-- after deploying the code purge.

BEGIN;

DROP TABLE IF EXISTS processed_events CASCADE;
DROP TABLE IF EXISTS write_outbox CASCADE;

COMMIT;

