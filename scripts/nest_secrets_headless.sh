#!/usr/bin/env bash
# Load Nest Device Access secrets from 1Password HEADLESSLY (#85 #93).
#
# Headless service-account auth only: OP_SERVICE_ACCOUNT_TOKEN authenticates the CLI
# non-interactively — no `op signin`, no biometric unlock, no desktop app — so this runs
# unattended in CI, over SSH, or on the second machine.
# Source: https://www.1password.dev/service-accounts/use-with-1password-cli/ (fetched 2026-09-08)
#
# Usage:
#   export OP_SERVICE_ACCOUNT_TOKEN=...            # from the 1Password service account
#   eval "$(bash scripts/nest_secrets_headless.sh export)"   # secrets → this shell's env
#   bash scripts/nest_secrets_headless.sh check              # names + presence only, no values
#   bash scripts/nest_secrets_headless.sh template           # write the op:// reference template
#
# VALUE DISCIPLINE: values flow op → env (or a 0600 temp file) and are NEVER printed,
# echoed, logged, or written into the repo. `check` prints names and set/unset only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VAULT="${VAULT:-dev}"
ITEM="${NEST_OP_ITEM:-IoT-ASP Nest Device Access}"
TEMPLATE="${NEST_TEMPLATE:-.github/nest.op.env}"

# Secret NAMES only — mirrors iot_asp_autoroute/nest/constants.py SECRET_NAMES.
NAMES=(
  NEST_DA_PROJECT_ID
  NEST_OAUTH_CLIENT_ID
  NEST_OAUTH_CLIENT_SECRET
  NEST_REFRESH_TOKEN
  NEST_PUBSUB_SUBSCRIPTION
  NEST_DA_OWNER_ACCOUNT
)

fail() { echo "FAIL: $*" >&2; exit 1; }

require_headless_op() {
  command -v op >/dev/null 2>&1 || fail "op not installed (brew install 1password-cli)"
  [[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]] \
    || fail "OP_SERVICE_ACCOUNT_TOKEN is not set. This script is headless-only by design — create a 1Password service account, grant it the '$VAULT' vault, and export its token. Do not use 'op signin'."
  # Service accounts verify with `op user get --me` (Type: SERVICE_ACCOUNT), not `op whoami`.
  op user get --me >/dev/null 2>&1 \
    || fail "OP_SERVICE_ACCOUNT_TOKEN rejected — check the token and that vault '$VAULT' is granted to the service account"
}

cmd="${1:-check}"

case "$cmd" in
  check)
    require_headless_op
    echo "op: headless service account OK (vault '$VAULT')"
    printf '%-28s %s\n' "SECRET NAME" "IN ENV"
    for n in "${NAMES[@]}"; do
      if [[ -n "${!n:-}" ]]; then printf '%-28s %s\n' "$n" "set"; else printf '%-28s %s\n' "$n" "unset"; fi
    done
    echo "(presence only — values are never printed by this script)"
    ;;

  export)
    # Emit `export NAME=value` lines for `eval`. Written to stdout ONLY so the caller can
    # eval it; never redirect this into a file inside the repo.
    require_headless_op >&2
    for n in "${NAMES[@]}"; do
      # --vault is required when the service account can see more than one vault.
      if val="$(op read "op://${VAULT}/${ITEM}/${n}" 2>/dev/null)"; then
        printf 'export %s=%q\n' "$n" "$val"
      else
        printf '# %s not found at op://%s/%s/%s\n' "$n" "$VAULT" "$ITEM" "$n"
      fi
    done
    ;;

  template)
    # A dotenv of op:// REFERENCES (not values) for `op inject`. Safe to read; still
    # gitignored, because references disclose vault/item structure.
    [[ -f "$TEMPLATE" ]] && fail "$TEMPLATE already exists — refusing to overwrite"
    mkdir -p "$(dirname "$TEMPLATE")"
    {
      echo "# op:// references for the Nest Device Access secrets — NO VALUES."
      echo "# Resolve headlessly: OP_SERVICE_ACCOUNT_TOKEN=... op inject -i $TEMPLATE"
      for n in "${NAMES[@]}"; do
        echo "${n}=op://${VAULT}/${ITEM}/${n}"
      done
    } > "$TEMPLATE"
    chmod 600 "$TEMPLATE"
    echo "wrote $TEMPLATE (references only, mode 600)"
    ;;

  *)
    sed -n '2,17p' "$0"
    exit 2
    ;;
esac

echo "OK nest_secrets_headless"
