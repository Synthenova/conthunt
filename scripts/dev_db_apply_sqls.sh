#!/usr/bin/env bash
set -euo pipefail

# Apply the legacy SQL migrations in backend/.sqls to the local docker Postgres,
# in filename-sorted order (001.sql, 002_..., ...).
#
# This bypasses Alembic and is useful to unblock local dev if the baseline replay
# is failing. Runs against Postgres directly (5432), not PgBouncer.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.db.yml"
SCHEMA="${DB_SCHEMA:-conthunt}"
SQLS_DIR="$ROOT_DIR/backend/.sqls"

if [[ ! -d "$SQLS_DIR" ]]; then
  echo "Missing $SQLS_DIR" >&2
  exit 1
fi

files=()
while IFS= read -r -d '' f; do
  files+=("$f")
done < <(find "$SQLS_DIR" -maxdepth 1 -type f -name '*.sql' -print0 | LC_ALL=C sort -z)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No .sql files found in $SQLS_DIR" >&2
  exit 1
fi

echo "Applying ${#files[@]} legacy SQL migrations to schema '$SCHEMA'..."

for f in "${files[@]}"; do
  rel="${f#$ROOT_DIR/}"
  echo "-> $rel"
  {
    echo "SET client_min_messages TO warning;"
    echo "CREATE SCHEMA IF NOT EXISTS ${SCHEMA};"
    echo "SET search_path TO ${SCHEMA}, public;"
    cat "$f"
    echo
  } | docker compose -f "$COMPOSE_FILE" exec -T postgres \
      psql -v ON_ERROR_STOP=1 -U conthunt_service -d postgres >/dev/null
done

echo "Done."

