#!/usr/bin/env bash
set -euo pipefail

# WARNING: This deletes the local Postgres data volume.
docker compose -f docker-compose.db.yml down -v
# Data is a bind mount (./docker/postgres-data), so "down -v" is not enough.
rm -rf docker/postgres-data
docker compose -f docker-compose.db.yml up -d --build

# Bootstrap schema from legacy SQL migrations (until everything is fully Alembic-managed).
./scripts/dev_db_apply_sqls.sh

# Mark the bootstrapped schema as the Alembic baseline so future revisions can apply cleanly.
docker compose -f docker-compose.db.yml --profile tools run --rm migrate \
  "pip install -r requirements.migrations.txt >/dev/null && alembic stamp head"

docker compose -f docker-compose.db.yml ps
