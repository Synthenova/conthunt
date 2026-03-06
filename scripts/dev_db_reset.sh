#!/usr/bin/env bash
set -euo pipefail

# WARNING: This deletes the local Postgres data volume.
docker compose -f docker-compose.db.yml down -v
# Data is a bind mount (./docker/postgres-data), so "down -v" is not enough.
rm -rf docker/postgres-data
docker compose -f docker-compose.db.yml up -d --build

# Build a fresh local database directly from Alembic.
docker compose -f docker-compose.db.yml --profile tools run --rm migrate \
  "pip install -r requirements.migrations.txt >/dev/null && alembic upgrade head"

docker compose -f docker-compose.db.yml ps
