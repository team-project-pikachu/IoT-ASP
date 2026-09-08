#!/usr/bin/env bash
# M8 — gcloud bootstrap checks for Home APIs / Vertex / Gemini Enterprise + SDM/PubSub path.
# Default: DRY-RUN (print + check identity). --apply only after explicit owner confirmation.
# Never prints secrets or raw account emails. Does not invent OAuth client IDs.
set -euo pipefail

APPLY=0
OWNER_EMAIL="${HOME_APIS_OWNER_EMAIL:-betty@bearresearch.io}"

usage() {
  cat <<'EOF'
Usage: scripts/home_apis_gcloud_bootstrap.sh [--apply]

  (default)  Print gcloud auth/project and required service names; no mutations.
  --apply    Attempt `gcloud services enable` for documented APIs (OWNER CONFIRMATION).

Owner identity (Google Home / Nest premium + GCP): betty@bearresearch.io
OAuth client / IAP: configure in Google Home Developer Console + GCP console (owner-gated).
1Password: use `dev` vault item *names* only — never paste tokens into git.
Project: prefers $GOOGLE_CLOUD_PROJECT, else active gcloud config.
EOF
}

for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    --apply) APPLY=1 ;;
    *) echo "Unknown arg: $arg" >&2; usage; exit 2 ;;
  esac
done

command -v gcloud >/dev/null 2>&1 || {
  echo "FAIL: gcloud not on PATH" >&2
  exit 2
}

echo "=== gcloud identity (dry check; emails redacted in logs) ==="
ACCOUNT="$(gcloud config get-value account 2>/dev/null || true)"
PROJECT="${GOOGLE_CLOUD_PROJECT:-}"
if [[ -z "$PROJECT" || "$PROJECT" == "(unset)" ]]; then
  PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
fi
if [[ -n "$ACCOUNT" ]]; then
  echo "account_configured=yes"
else
  echo "account_configured=no"
fi
echo "project=${PROJECT:-<unset>}"
echo "expected_owner_configured=yes"
ACCOUNT_MATCH=0
if [[ -n "$ACCOUNT" && "$ACCOUNT" == "$OWNER_EMAIL" ]]; then
  ACCOUNT_MATCH=1
  echo "owner_account_match=yes"
elif [[ -n "$ACCOUNT" ]]; then
  echo "owner_account_match=no"
else
  echo "owner_account_match=unknown"
fi
if [[ -n "$ACCOUNT" && "$ACCOUNT" != "$OWNER_EMAIL" ]]; then
  if [[ "$APPLY" -eq 1 ]]; then
    echo "FAIL: active gcloud account does not match HOME_APIS_OWNER_EMAIL; refusing --apply" >&2
    exit 1
  fi
  echo "NOTE: active gcloud account differs from Nest/Home owner email (OK for CI dry-check)."
fi

echo
echo "=== ADC / auth status (no account emails printed) ==="
ACTIVE_STATUS="$(gcloud auth list --filter=status:ACTIVE --format='value(status)' 2>/dev/null | head -n 1 || true)"
if [[ -n "$ACTIVE_STATUS" ]]; then
  echo "active_credential_status=${ACTIVE_STATUS}"
else
  echo "active_credential_status=<none>"
fi

echo
echo "=== Required / related API service names (document only) ==="
# Vertex + SDM CameraSound → Pub/Sub → detector path (#103)
SERVICES=(
  aiplatform.googleapis.com
  pubsub.googleapis.com
  smartdevicemanagement.googleapis.com
)
for s in "${SERVICES[@]}"; do
  echo " - $s"
done
echo "Home APIs iOS OAuth / Device & Automation: Google Home Developer Console (not a gcloud services enable alone)."
echo "CLI surfaces to explore later: gcloud ai … ; gcloud beta ai … ; gcloud alpha ai …"

echo
echo "=== Enablement commands (printed; applied only with --apply) ==="
for s in "${SERVICES[@]}"; do
  echo "gcloud services enable ${s} --project=\${PROJECT}"
done

if [[ "$APPLY" -eq 0 ]]; then
  echo
  echo "DRY-RUN complete. Re-run with --apply after owner confirmation to enable APIs."
  exit 0
fi

if [[ -z "$PROJECT" || "$PROJECT" == "(unset)" ]]; then
  echo "FAIL: set GOOGLE_CLOUD_PROJECT or gcloud project before --apply" >&2
  exit 1
fi

if [[ "$ACCOUNT_MATCH" -ne 1 ]]; then
  echo "FAIL: owner account match required before --apply" >&2
  exit 1
fi

echo
echo "APPLY: enabling services on project=${PROJECT}"
for s in "${SERVICES[@]}"; do
  gcloud services enable "$s" --project="$PROJECT"
done
echo "OK apply finished. Configure OAuth client + Nest devices in consoles (org identity)."
