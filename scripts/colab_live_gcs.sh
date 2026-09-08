#!/usr/bin/env bash
# Colab / CLI live GCS features (#26) — dry-run by default.
# Secret NAMES only: LIVE_GCS, IOT_ASP_GCS_BUCKET, GCP_SA_JSON, GOOGLE_CLOUD_PROJECT.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/services/autoroute-adk${PYTHONPATH:+:$PYTHONPATH}"
NODE="${IOT_ASP_NODE:-node1}"
LIMIT="${IOT_ASP_LIMIT:-50}"
ARGS=(--node "$NODE" --limit "$LIMIT")

if [[ "${LIVE_GCS:-0}" == "1" ]]; then
  if [[ -z "${IOT_ASP_GCS_BUCKET:-}" ]]; then
    echo "LIVE_GCS=1 requires IOT_ASP_GCS_BUCKET. No credentials invented." >&2
    exit 2
  fi
  ARGS+=(--live)
  echo "# live: will write meta/features only under bucket name IOT_ASP_GCS_BUCKET (value not printed)"
else
  export IOT_ASP_AUTOROUTE_DRY_RUN=1
  export IOT_ASP_AUTOROUTE_DRY_ROOT="${IOT_ASP_AUTOROUTE_DRY_ROOT:-${ROOT}/.autoroute-dry}"
  mkdir -p "$IOT_ASP_AUTOROUTE_DRY_ROOT"
  ARGS+=(--seed-demo)
  echo "# dry-run mirror: $IOT_ASP_AUTOROUTE_DRY_ROOT"
fi

exec python3 -m iot_asp_autoroute.features_live "${ARGS[@]}"
