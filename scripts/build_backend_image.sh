#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-conthunt-dev}"
REGION="${REGION:-us-central1}"
REPOSITORY="${REPOSITORY:-conthunt-backend}"
IMAGE_NAME="${IMAGE_NAME:-app}"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "$(dirname "$0")/.." rev-parse --short HEAD)}"
IMAGE="${IMAGE:-${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}}"

gcloud builds submit backend \
  --project="${PROJECT_ID}" \
  --tag="${IMAGE}"

printf '%s\n' "${IMAGE}"
