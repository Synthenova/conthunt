#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-conthunt-dev}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-conthunt}"
REPOSITORY="${REPOSITORY:-conthunt-backend}"
IMAGE_NAME="${IMAGE_NAME:-app}"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "$(dirname "$0")/.." rev-parse --short HEAD)}"
IMAGE="${IMAGE:-${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}}"
ENV_FILE="${ENV_FILE:-backend/.env.dev}"
MEMORY="${MEMORY:-1Gi}"
CPU="${CPU:-1}"
TIMEOUT="${TIMEOUT:-3600}"
CONCURRENCY="${CONCURRENCY:-80}"
MAX_INSTANCES="${MAX_INSTANCES:-5}"
ALLOW_UNAUTHENTICATED="${ALLOW_UNAUTHENTICATED:-true}"
SIGNER_SECRET_NAME="${SIGNER_SECRET_NAME:-gcs-url-signer-key}"
SIGNER_SECRET_PATH="${SIGNER_SECRET_PATH:-/secrets/gcs-signer/key.json}"
TMP_ENV_YAML="$(mktemp /tmp/conthunt-env.XXXXXX.yaml)"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing env file: ${ENV_FILE}" >&2
  exit 1
fi

cleanup() {
  rm -f "${TMP_ENV_YAML}"
}
trap cleanup EXIT

python3 - "${ENV_FILE}" "${TMP_ENV_YAML}" <<'PY'
import json
import pathlib
import sys

src = pathlib.Path(sys.argv[1])
dst = pathlib.Path(sys.argv[2])

entries = []
for raw in src.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    entries.append((key, value))

with dst.open("w", encoding="utf-8") as fh:
    for key, value in entries:
        fh.write(f"{key}: {json.dumps(value)}\n")
PY

DEPLOY_FLAGS=(
  --project="${PROJECT_ID}"
  --region="${REGION}"
  --platform=managed
  --image="${IMAGE}"
  --memory="${MEMORY}"
  --cpu="${CPU}"
  --timeout="${TIMEOUT}"
  --concurrency="${CONCURRENCY}"
  --max-instances="${MAX_INSTANCES}"
  --env-vars-file="${TMP_ENV_YAML}"
  --update-secrets="${SIGNER_SECRET_PATH}=${SIGNER_SECRET_NAME}:latest"
)

if [[ "${ALLOW_UNAUTHENTICATED}" == "true" ]]; then
  DEPLOY_FLAGS+=(--allow-unauthenticated)
fi

gcloud run deploy "${SERVICE}" "${DEPLOY_FLAGS[@]}"
