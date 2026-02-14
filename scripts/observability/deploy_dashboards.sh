#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DASHBOARD_DIR="${ROOT_DIR}/observability/gcp/dashboards"

if [[ "${DEPLOY_DASHBOARDS:-false}" != "true" ]]; then
  echo "[dashboards] DEPLOY_DASHBOARDS is not true. Skipping dashboard deployment."
  exit 0
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "[dashboards] gcloud is required." >&2
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
if [[ -z "${PROJECT_ID}" ]]; then
  echo "[dashboards] PROJECT_ID is required." >&2
  exit 1
fi

for file in "${DASHBOARD_DIR}"/*.json; do
  [[ -f "${file}" ]] || continue

  display_name="$(sed -n 's/.*"displayName": *"\([^"]*\)".*/\1/p' "${file}" | head -n1)"
  if [[ -z "${display_name}" ]]; then
    echo "[dashboards] Missing displayName in ${file}, skipping." >&2
    continue
  fi

  existing_name="$(gcloud monitoring dashboards list --project "${PROJECT_ID}" --filter="displayName=\"${display_name}\"" --format='value(name)' | head -n1 || true)"

  if [[ -n "${existing_name}" ]]; then
    echo "[dashboards] Updating ${display_name} (${existing_name})"
    gcloud monitoring dashboards update "${existing_name}" \
      --project "${PROJECT_ID}" \
      --config-from-file "${file}" >/dev/null
  else
    echo "[dashboards] Creating ${display_name}"
    gcloud monitoring dashboards create \
      --project "${PROJECT_ID}" \
      --config-from-file "${file}" >/dev/null
  fi

done

echo "[dashboards] Dashboard deployment complete."
