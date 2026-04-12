#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-conthunt-dev}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-conthunt-frontend}"
SOURCE_DIR="${SOURCE_DIR:-frontend}"
ALLOW_UNAUTHENTICATED="${ALLOW_UNAUTHENTICATED:-true}"
export PROJECT_ID
TMP_BUILD_ENV_YAML="$(mktemp /tmp/conthunt-frontend-build-env.XXXXXX.yaml)"

secret_value() {
  local secret_name="$1"
  gcloud secrets versions access latest \
    --project="${PROJECT_ID}" \
    --secret="${secret_name}"
}

cleanup() {
  rm -f "${TMP_BUILD_ENV_YAML}"
}
trap cleanup EXIT

NEXT_PUBLIC_FIREBASE_API_KEY="$(secret_value NEXT_PUBLIC_FIREBASE_API_KEY)"
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="$(secret_value NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN)"
NEXT_PUBLIC_FIREBASE_APP_ID="$(secret_value NEXT_PUBLIC_FIREBASE_APP_ID)"
NEXT_PUBLIC_BACKEND_URL="$(secret_value NEXT_PUBLIC_BACKEND_URL)"
NEXT_PUBLIC_WHOP_APP_ID="$(secret_value NEXT_PUBLIC_WHOP_APP_ID)"
NEXT_PUBLIC_POSTHOG_KEY="$(secret_value NEXT_PUBLIC_POSTHOG_KEY)"
NEXT_PUBLIC_POSTHOG_HOST="$(secret_value NEXT_PUBLIC_POSTHOG_HOST)"

export NEXT_PUBLIC_FIREBASE_API_KEY
export NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
export NEXT_PUBLIC_FIREBASE_APP_ID
export NEXT_PUBLIC_BACKEND_URL
export NEXT_PUBLIC_WHOP_APP_ID
export NEXT_PUBLIC_POSTHOG_KEY
export NEXT_PUBLIC_POSTHOG_HOST

python3 - "${TMP_BUILD_ENV_YAML}" <<'PY'
import json
import pathlib
import os
import sys

path = pathlib.Path(sys.argv[1])
values = {
    "NEXT_PUBLIC_FIREBASE_API_KEY": os.environ["NEXT_PUBLIC_FIREBASE_API_KEY"],
    "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN": os.environ["NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN"],
    "NEXT_PUBLIC_FIREBASE_PROJECT_ID": os.environ.get("PROJECT_ID", ""),
    "NEXT_PUBLIC_FIREBASE_APP_ID": os.environ["NEXT_PUBLIC_FIREBASE_APP_ID"],
    "NEXT_PUBLIC_BACKEND_URL": os.environ["NEXT_PUBLIC_BACKEND_URL"],
    "NEXT_PUBLIC_WHOP_APP_ID": os.environ["NEXT_PUBLIC_WHOP_APP_ID"],
    "NEXT_PUBLIC_POSTHOG_KEY": os.environ["NEXT_PUBLIC_POSTHOG_KEY"],
    "NEXT_PUBLIC_POSTHOG_HOST": os.environ["NEXT_PUBLIC_POSTHOG_HOST"],
}

with path.open("w", encoding="utf-8") as fh:
    for key, value in values.items():
        fh.write(f"{key}: {json.dumps(value)}\n")
PY

DEPLOY_FLAGS=(
  --project="${PROJECT_ID}"
  --region="${REGION}"
  --source="${SOURCE_DIR}"
  --build-env-vars-file="${TMP_BUILD_ENV_YAML}"
  --set-env-vars="GCLOUD_PROJECT=${PROJECT_ID}"
  --set-secrets="WHOP_API_KEY=WHOP_API_KEY:latest"
)

if [[ "${ALLOW_UNAUTHENTICATED}" == "true" ]]; then
  DEPLOY_FLAGS+=(--allow-unauthenticated)
fi

gcloud run deploy "${SERVICE}" "${DEPLOY_FLAGS[@]}"
