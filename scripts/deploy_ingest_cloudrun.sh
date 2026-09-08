#!/usr/bin/env bash
# Deploy Cloud Run ingest for #61 (phones → POST /ingest → GCS).
# Credential path: ADC / gcloud user; bucket name via env — never print secret values.
#
# NOTE: Org policy iam.allowedPolicyMemberDomains blocks allUsers invoker on this
# project. Public 3-phone beacons use Vercel api/ingest.js instead; this Cloud Run
# service remains for authenticated ADK / operator proxy (#60).
#
# Phones use navigator.sendBeacon (no Authorization header). The service MUST
# allow unauthenticated invoke (`--allow-unauthenticated` / allUsers run.invoker).
# Do not bake Vertex/ADK keys into the PWA; only this public HTTPS surface.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${ROOT}/services/autoroute-adk"
PROJECT="${GOOGLE_CLOUD_PROJECT:-bear-iot-asp-rec}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE="${IOT_ASP_INGEST_SERVICE:-iot-asp-ingest}"
BUCKET="${IOT_ASP_GCS_BUCKET:-iot-asp-recordings-bear-20260907}"
TAG="${IOT_ASP_INGEST_TAG:-61}"

if [[ ! -f "${SRC}/Dockerfile" || ! -f "${SRC}/ingest_app.py" ]]; then
  echo "missing ingest Cloud Run sources under services/autoroute-adk/" >&2
  exit 1
fi

if [[ -z "${BUCKET}" ]]; then
  echo "IOT_ASP_GCS_BUCKET must be set (private bucket name)." >&2
  exit 1
fi

echo "# deploy ${SERVICE} → project=${PROJECT} region=${REGION} tag=${TAG}"
# Bucket name is infrastructure id (not a key); still avoid dumping env wholesale.
gcloud run deploy "${SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --source="${SRC}" \
  --allow-unauthenticated \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --max-instances=3 \
  --min-instances=0 \
  --timeout=60 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT},IOT_ASP_GCS_BUCKET=${BUCKET},IOT_ASP_AUTOROUTE_DRY_RUN=0,IOT_ASP_AUTOROUTE_ON_INGEST=0" \
  --quiet

URL="$(gcloud run services describe "${SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='value(status.url)')"

echo "INGEST_URL=${URL}"
echo "TELEMETRY_URL=${URL}/ingest"
echo "PATCH_URL=${URL}/patch.json"
echo "# Phone field URL (no secrets):"
echo "#   https://<vercel>/?telemetry=${URL}/ingest&patch=${URL}/patch.json&pollMs=3000"
echo "# Or set BACKEND_BASE_URL=\"${URL}\" in public/index.html (still no keys) and redeploy Vercel."
echo "# health:"
curl -sS -o /dev/null -w "healthz HTTP %{http_code}\n" "${URL}/healthz" || true
INVOKERS="$(gcloud run services get-iam-policy "${SERVICE}" \
  --project="${PROJECT}" --region="${REGION}" \
  --flatten='bindings[].members' \
  --filter='bindings.role:roles/run.invoker' \
  --format='value(bindings.members)' 2>/dev/null || true)"
if ! grep -q 'allUsers\|allAuthenticatedUsers' <<<"${INVOKERS}"; then
  echo "# WARN: no allUsers invoker — phone sendBeacon will 403. Re-run with --allow-unauthenticated or:" >&2
  echo "#   gcloud run services add-iam-policy-binding ${SERVICE} --project=${PROJECT} --region=${REGION} --member=allUsers --role=roles/run.invoker" >&2
fi
