#!/usr/bin/env bash
# #60 — ADK / Cloud Run deploy dry-check (names + files only; never deploys).
# Exit 0 when local package layout + docs look deployable; 1 on structural gaps.
# Does NOT call gcloud / adk deploy / invent project IDs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

missing=0
need() {
  if [[ -e "$1" ]]; then echo "OK $1"; else echo "MISSING $1"; missing=$((missing + 1)); fi
}

echo "# ADK package layout"
need services/autoroute-adk/iot_asp_autoroute/agent.py
need services/autoroute-adk/iot_asp_autoroute/tools.py
need services/autoroute-adk/iot_asp_autoroute/clamps.py
need services/autoroute-adk/ingest_main.py
need services/autoroute-adk/requirements.txt
need scripts/autoroute_dev.sh
need docs/adk-autoroute.md
need docs/api-contract.md

echo "# names-only env (presence in this shell — values never printed)"
for name in GOOGLE_CLOUD_PROJECT GOOGLE_CLOUD_LOCATION IOT_ASP_GCS_BUCKET IOT_ASP_GEMINI_ENGINE_ID; do
  if [[ -n "${!name:+x}" ]]; then echo "$name: set"; else echo "$name: unset (ok for dry-check)"; fi
done

cat <<'EOF'

# Owner next (not run by this script)
#   bash scripts/autoroute_dev.sh
#   # then: adk deploy cloud_run | agent_engine per docs/adk-autoroute.md
# Never commit SA JSON; use 1Password / Secret Manager names only.
EOF

if (( missing > 0 )); then
  echo "FAIL: ${missing} required path(s) missing (issue #60)" >&2
  exit 1
fi
echo "OK adk_deploy_dry_check"
