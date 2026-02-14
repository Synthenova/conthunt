#!/usr/bin/env bash
set -euo pipefail

docker compose -f docker-compose.db.yml up -d
docker compose -f docker-compose.db.yml ps

