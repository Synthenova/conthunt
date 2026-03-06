#!/usr/bin/env bash
set -euo pipefail

# One-time switch script for environments that already contain the application
# schema but do not yet have Alembic history recorded.
#
# Required env:
#   DATABASE_URL=postgresql+asyncpg://... (or postgresql://...)
# Optional env:
#   DB_SCHEMA=conthunt
#   APP_ENV=local
#
# Usage:
#   DATABASE_URL='postgresql+asyncpg://...' DB_SCHEMA=conthunt ./scripts/alembic_bootstrap_existing_db.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "Missing DATABASE_URL. Set it to the target DB URL first." >&2
  exit 1
fi

export DB_SCHEMA="${DB_SCHEMA:-conthunt}"
export APP_ENV="${APP_ENV:-local}"

if ! command -v alembic >/dev/null 2>&1; then
  echo "alembic not found on PATH." >&2
  echo "Install migration deps first:" >&2
  echo "  cd backend && pip install -r requirements.migrations.txt" >&2
  exit 1
fi

cd "$BACKEND_DIR"

echo "Target schema: $DB_SCHEMA"
echo "Step 1/2: stamp baseline revision (0001_initial)"
alembic stamp 0001_initial

echo "Step 2/2: apply all Alembic revisions after baseline"
alembic upgrade head

echo "Done. Current revision:"
alembic current
