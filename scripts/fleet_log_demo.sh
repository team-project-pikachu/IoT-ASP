#!/usr/bin/env bash
# #22 offline fleet_log dry-run demo — writes meta/logs under .autoroute-dry (no GCS, no secrets).
# Usage: bash scripts/fleet_log_demo.sh [node]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NODE="${1:-node1}"
export PYTHONPATH="${ROOT}/services/autoroute-adk${PYTHONPATH:+:$PYTHONPATH}"
export IOT_ASP_AUTOROUTE_DRY_RUN=1
export IOT_ASP_AUTOROUTE_DRY_ROOT="${IOT_ASP_AUTOROUTE_DRY_ROOT:-${ROOT}/.autoroute-dry}"
mkdir -p "$IOT_ASP_AUTOROUTE_DRY_ROOT"
echo "# dry-run root: $IOT_ASP_AUTOROUTE_DRY_ROOT (values of bucket/SA never printed)"
exec python3 -m iot_asp_autoroute.fleet_log --demo --node "$NODE"
