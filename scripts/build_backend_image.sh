#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-conthunt-dev}"
IMAGE="${IMAGE:-us-central1-docker.pkg.dev/${PROJECT_ID}/conthunt-backend/app}"

gcloud builds submit backend \
  --project="${PROJECT_ID}" \
  --tag="${IMAGE}" \
  --async
