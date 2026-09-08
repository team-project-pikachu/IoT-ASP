#!/usr/bin/env bash
# M8 — gcloud bootstrap checks for Home APIs / Vertex / Gemini Enterprise wiring.
# Default: DRY-RUN (print + check identity). --apply only after explicit owner confirmation.
# Never prints secrets. Does not invent OAuth client IDs.
set -euo pipefail

APPLY=0
OWNER_EMAIL="${HOME_APIS_OWNER_EMAIL:-bettyctai@gmail.com}"

usage() {
  cat <<'EOF'
Usage: scripts/home_apis_gcloud_bootstrap.sh [--apply]

  (default)  Print gcloud auth/project and required service names; no mutations.
  --apply    Attempt `gcloud services enable` for documented APIs (OWNER CONFIRMATION).

Owner identity (Google Home / Nest premium + GCP): bettyctai@gmail.com
OAuth client / IAP: configure in Google Home Developer Console + GCP console (owner-gated).
1Password: use `dev` vault item *names* only — never paste tokens into git.
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

echo "=== gcloud identity (dry check) ==="
ACCOUNT="$(gcloud config get-value account 2>/dev/null || true)"
PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
echo "account=${ACCOUNT:-<unset>}"
echo "project=${PROJECT:-<unset>}"
echo "expected_owner_email=${OWNER_EMAIL}"
if [[ -n "$ACCOUNT" && "$ACCOUNT" != "$OWNER_EMAIL" ]]; then
  echo "NOTE: active gcloud account differs from Nest/Home owner email (OK for CI dry-check)."
fi

echo
echo "=== ADC / auth status (no tokens printed) ==="
gcloud auth list --format='value(account,status)' 2>/dev/null || echo "(auth list unavailable)"

echo
echo "=== Required / related API service names (document only) ==="
# Names from gcloud help surfaces: aiplatform, and Home/Nest OAuth are console-side.
SERVICES=(
  aiplatform.googleapis.com
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
  echo "FAIL: set gcloud project before --apply" >&2
  exit 1
fi

echo
echo "APPLY: enabling services on project=${PROJECT}"
for s in "${SERVICES[@]}"; do
  gcloud services enable "$s" --project="$PROJECT"
done
echo "OK apply finished. Configure OAuth client + Nest devices as ${OWNER_EMAIL} in consoles."
