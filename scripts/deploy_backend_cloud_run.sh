#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-conthunt-dev}"
SERVICE="${SERVICE:-conthunt}"
REGION="${REGION:-us-central1}"
IMAGE="${IMAGE:-us-central1-docker.pkg.dev/${PROJECT_ID}/conthunt-backend/app}"
ENV_FILE="${ENV_FILE:-backend/.env.prod}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing env file: ${ENV_FILE}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

: "${UPSTASH_REDIS_REST_URL:?UPSTASH_REDIS_REST_URL is required in ${ENV_FILE}}"
: "${UPSTASH_REDIS_REST_TOKEN:?UPSTASH_REDIS_REST_TOKEN is required in ${ENV_FILE}}"
: "${GEMINI_ANALYSIS_TIMEOUT_S:=420}"

gcloud run deploy "${SERVICE}" \
  --project="${PROJECT_ID}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --platform=managed \
  --update-env-vars="UPSTASH_REDIS_REST_URL=${UPSTASH_REDIS_REST_URL},UPSTASH_REDIS_REST_TOKEN=${UPSTASH_REDIS_REST_TOKEN},GEMINI_ANALYSIS_TIMEOUT_S=${GEMINI_ANALYSIS_TIMEOUT_S},GCP_PROJECT=${PROJECT_ID},GCLOUD_PROJECT=${PROJECT_ID}" \
  --remove-secrets="REDIS_URL,REDIS_MAX_CONNECTIONS,DB_SEMAPHORE_ENABLED,DB_SEM_KEY_PREFIX,DB_SEM_TTL_MS,DB_SEM_API_LIMIT,DB_SEM_TASKS_LIMIT,DB_SEM_API_MAX_WAIT_MS,DB_SEM_TASKS_MAX_WAIT_MS"
