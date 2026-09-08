#!/usr/bin/env bash
# Idempotent GCP bootstrap for the Nest Device Access (SDM) event path (#85 #92 #93).
#
# DRY RUN BY DEFAULT: prints the exact plan and mutates nothing, so CI can run it with
# no credentials. Pass --apply to execute (owner, authenticated as a project admin).
#
# Every command below is transcribed from a fetched vendor page; sources are inline.
# No secret VALUES are read, printed or stored by this script — only secret NAMES.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROJECT="${GOOGLE_CLOUD_PROJECT:-bear-iot-asp-rec}"
TOPIC="${NEST_PUBSUB_TOPIC:-iot-asp-nest-events}"
SUBSCRIPTION="${NEST_PUBSUB_SUBSCRIPTION_ID:-iot-asp-nest-events-sub}"
SA_NAME="${NEST_POLLER_SA:-iot-asp-nest-poller}"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"

# The Device Access owner is a CONSUMER Google Account (Workspace is not supported —
# https://developers.google.com/nest/device-access/get-started). Its address is site
# PII under CLAUDE.md invariant 7, so it is NEVER hardcoded here: export it, or read it
# from 1Password Environment `dev` item NEST_DA_OWNER_ACCOUNT. Empty = skip that step.
OWNER_ACCOUNT="${NEST_DA_OWNER_ACCOUNT:-}"

# The Google-managed principal that publishes SDM events into a self-hosted topic.
# It is a GOOGLE GROUP, not a service account — `serviceAccount:` here fails SILENTLY
# with zero events delivered forever. Verified verbatim from the vendor page:
#   gcloud pubsub topics add-iam-policy-binding projects/{project}/topics/{topic} \
#     --member="group:sdm-publisher@googlegroups.com" --role="roles/pubsub.publisher"
# Source: https://developers.google.com/nest/device-access/subscribe-to-events
SDM_PUBLISHER_MEMBER="group:sdm-publisher@googlegroups.com"

APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --dry-run) APPLY=0 ;;
    -h|--help)
      sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

step() { printf '\n\033[1m› %s\033[0m\n' "$*"; }
run() {
  printf '  %s\n' "$*"
  if [[ "$APPLY" == "1" ]]; then
    # Idempotent: ALREADY_EXISTS is success for create-style calls.
    if ! "$@" 2>/tmp/nest_bootstrap_err.$$; then
      if grep -qiE 'already exists|ALREADY_EXISTS' /tmp/nest_bootstrap_err.$$; then
        echo "    (already exists — ok)"
      else
        cat /tmp/nest_bootstrap_err.$$ >&2
        rm -f /tmp/nest_bootstrap_err.$$
        return 1
      fi
    fi
    rm -f /tmp/nest_bootstrap_err.$$
  fi
}

if [[ "$APPLY" == "1" ]] && ! command -v gcloud >/dev/null 2>&1; then
  echo "FAIL: --apply requires the gcloud CLI on PATH" >&2
  exit 1
fi

echo "IoT-ASP Nest Device Access bootstrap"
echo "  project      : $PROJECT"
echo "  topic        : $TOPIC"
echo "  subscription : $SUBSCRIPTION"
echo "  poller SA    : $SA_EMAIL"
echo "  mode         : $([[ "$APPLY" == "1" ]] && echo APPLY || echo 'DRY RUN (pass --apply to execute)')"

step "1. Enable the APIs this integration needs"
# smartdevicemanagement: the SDM API itself
#   https://developers.google.com/nest/device-access/get-started
# pubsub: the event transport (self-hosted topic, post-Jan-2025 projects)
# secretmanager: refresh token / client secret storage
# discoveryengine + aiplatform: Gemini Enterprise engine + Agent Platform / Colab
#   (docs/gemini-enterprise.md)
run gcloud services enable \
  smartdevicemanagement.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  discoveryengine.googleapis.com \
  aiplatform.googleapis.com \
  --project="$PROJECT"

step "2. Create the self-hosted Pub/Sub topic"
# --message-retention-duration=0s is the value the vendor page shows.
run gcloud pubsub topics create "$TOPIC" --project="$PROJECT" --message-retention-duration=0s

step "3. Let the SDM service publish into it (the highest-risk line in this script)"
run gcloud pubsub topics add-iam-policy-binding "projects/${PROJECT}/topics/${TOPIC}" \
  --member="$SDM_PUBLISHER_MEMBER" \
  --role="roles/pubsub.publisher" \
  --project="$PROJECT"

step "4. Create the pull subscription"
# --expiration-period=never: the 31-day default DELETES a subscription that goes quiet,
#   which a low-traffic research fleet will do.
# --ack-deadline=60: the 10s default is too short to map, classify and ingest an event.
# --message-retention-duration=7d: survive a weekend outage of the poller.
run gcloud pubsub subscriptions create "$SUBSCRIPTION" \
  --topic="projects/${PROJECT}/topics/${TOPIC}" \
  --ack-deadline=60 \
  --message-retention-duration=7d \
  --expiration-period=never \
  --project="$PROJECT"

step "5. Create the poller service account and give it the minimum role"
# roles/pubsub.subscriber grants pubsub.subscriptions.consume — required to pull AND
# to acknowledge. Bound on the SUBSCRIPTION, not project-wide.
# Source: https://docs.cloud.google.com/pubsub/docs/access-control
run gcloud iam service-accounts create "$SA_NAME" \
  --display-name="IoT-ASP Nest SDM event poller" \
  --project="$PROJECT"
run gcloud pubsub subscriptions add-iam-policy-binding "$SUBSCRIPTION" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/pubsub.subscriber" \
  --project="$PROJECT"

step "6. Create the secret CONTAINERS (names only — no values are written here)"
for secret in NEST_DA_PROJECT_ID NEST_OAUTH_CLIENT_ID NEST_OAUTH_CLIENT_SECRET NEST_REFRESH_TOKEN; do
  run gcloud secrets create "$secret" --replication-policy=automatic --project="$PROJECT"
done
run gcloud secrets add-iam-policy-binding NEST_REFRESH_TOKEN \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT"
echo "  NOTE: add each secret's VALUE yourself, e.g."
echo "        gcloud secrets versions add NEST_REFRESH_TOKEN --data-file=- --project=$PROJECT"
echo "        (values come from 1Password Environment 'dev'; never from this repo)"

step "7. Grant the Device Access owner account access to this project"
# The consumer account that owns the Nest devices must complete the SDM 3LO consent and
# is the account that will drive Agent Platform / Colab Enterprise notebooks.
# roles/aiplatform.colabEnterpriseUser is the documented minimum to create and run a
# Colab Enterprise notebook. Source: https://docs.cloud.google.com/colab/docs/access-control
if [[ -n "$OWNER_ACCOUNT" ]]; then
  run gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="user:${OWNER_ACCOUNT}" \
    --role="roles/aiplatform.colabEnterpriseUser"
  run gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="user:${OWNER_ACCOUNT}" \
    --role="roles/viewer"
else
  echo "  SKIPPED — NEST_DA_OWNER_ACCOUNT is unset."
  echo "  Run with the owner's consumer Google Account to grant Agent Platform / Colab access:"
  echo "    NEST_DA_OWNER_ACCOUNT=<owner@example.com> bash scripts/nest_gcp_bootstrap.sh --apply"
  echo "  Roles granted: roles/aiplatform.colabEnterpriseUser (create + run Colab Enterprise"
  echo "  notebooks at console.cloud.google.com/agent-platform/colab) and roles/viewer."
fi

step "8. Read back the bindings as verification evidence (.vv/nest/)"
# A read-back is the only proof the group: binding in step 3 actually landed. Capture
# this output into .vv/nest/EVIDENCE.md — it is the difference between "configured" and
# "believed to be configured".
run gcloud pubsub topics get-iam-policy "projects/${PROJECT}/topics/${TOPIC}" --project="$PROJECT"
run gcloud pubsub subscriptions describe "$SUBSCRIPTION" --project="$PROJECT"

step "9. Remaining OWNER-ONLY steps (browser; no agent performs these)"
cat <<'MANUAL'
  a. https://console.nest.google.com/device-access — pay the one-time US$5 fee, create
     the Device Access project, paste the OAuth Client ID, enable events, and register
     the Topic ID from step 2 above.
  b. Complete the PCM consent once, signed in as the account that owns the Nest devices:
     https://nestservices.google.com/partnerconnections/<DA-PROJECT-ID>/auth
       ?redirect_uri=https://www.google.com&access_type=offline&prompt=consent
       &client_id=<OAUTH-CLIENT-ID>&response_type=code
       &scope=https://www.googleapis.com/auth/sdm.service
     Exchange the code for a refresh token and store it as NEST_REFRESH_TOKEN.
  c. Make one devices.list call. Authorization is NOT complete until it succeeds, and
     until then the subscription stays empty and looks broken.
     Source: https://developers.google.com/nest/device-access/authorize
  See docs/nest-device-access.md for the full walkthrough.
MANUAL

echo
echo "OK nest_gcp_bootstrap"
