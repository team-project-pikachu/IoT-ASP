#!/usr/bin/env bash
# 1Password → GitHub Actions secrets bridge for the IoT-ASP continuous-ship pipeline.
#
# Deterministic, value-blind: secret VALUES flow op → temp file (0600) → gh, and are never
# printed, echoed, or left in shell history. Only NAMES and references appear on screen.
#
# Usage (run on the Mac where `op` and `gh` are signed in):
#   scripts/op_secrets_to_gh.sh discover            # list candidate Vercel items in the vault (titles only)
#   scripts/op_secrets_to_gh.sh template            # write .github/secrets.op.env from the example (edit refs)
#   scripts/op_secrets_to_gh.sh ids                 # VERCEL_ORG_ID / VERCEL_PROJECT_ID from `vercel link`
#   scripts/op_secrets_to_gh.sh hook                # create Vercel deploy hook, store URL in 1Password
#   scripts/op_secrets_to_gh.sh push [--dry-run]    # op inject template → gh secret set -f (all names)
#   scripts/op_secrets_to_gh.sh verify              # gh secret list (names only)
#
# Env overrides: REPO (owner/repo), VAULT (1Password vault), TEMPLATE (dotenv template with op:// refs),
#                VERCEL_SCOPE (team slug), VERCEL_PROJECT (project name), HOOK_NAME, HOOK_REF.
#
# Sources (verified 2026-09-08):
#   op read / op inject / op item: https://www.1password.dev/cli/reference (Context7 /websites/1password_dev_cli)
#   gh secret set -f <dotenv>, --body, stdin: https://cli.github.com/manual/gh_secret_set (Context7 /websites/cli_github_manual)
#   vercel link / deploy-hooks create --ref: Context7 /vercel/vercel (skills/vercel-cli references)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REPO="${REPO:-team-project-pikachu/IoT-ASP}"
VAULT="${VAULT:-dev}"
TEMPLATE="${TEMPLATE:-.github/secrets.op.env}"
EXAMPLE=".github/secrets.op.env.example"
VERCEL_SCOPE="${VERCEL_SCOPE:-1digital-design}"
VERCEL_PROJECT="${VERCEL_PROJECT:-hop-ultrasonic}"
HOOK_NAME="${HOOK_NAME:-gh-actions-prod}"
HOOK_REF="${HOOK_REF:-main}"
NAMES=(VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID VERCEL_DEPLOY_HOOK_PROD)

fail() { echo "FAIL: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "$1 not installed (brew install $2)"; }

need op 1password-cli
need gh gh

# Headless service-account auth is the DEFAULT and preferred path: OP_SERVICE_ACCOUNT_TOKEN
# authenticates the CLI non-interactively — no `op signin`, no biometric unlock, no desktop
# app — so this script runs unattended in CI, on a second machine, or over SSH.
# Verification for a service account is `op user get --me` (Type: SERVICE_ACCOUNT); `op whoami`
# is the interactive-session check. A service account must be GRANTED access to the vault, and
# `op item` needs --vault when it can see more than one.
# Source: https://www.1password.dev/service-accounts/use-with-1password-cli/ (fetched 2026-09-08)
if [[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
  op user get --me >/dev/null 2>&1 \
    || fail "OP_SERVICE_ACCOUNT_TOKEN is set but rejected — check the token and that vault '$VAULT' is granted to the service account"
  echo "op: headless service account (OP_SERVICE_ACCOUNT_TOKEN)"
else
  op whoami >/dev/null 2>&1 || fail "op not authenticated. Preferred: export OP_SERVICE_ACCOUNT_TOKEN=... (headless, no biometrics). Interactive fallback: eval \$(op signin)"
  echo "op: interactive session (set OP_SERVICE_ACCOUNT_TOKEN to run headless)"
fi
gh auth status >/dev/null 2>&1 || fail "gh not signed in — run: gh auth login"

cmd="${1:-help}"
shift || true

case "$cmd" in
  discover)
    echo "# 1Password items in vault '$VAULT' that look Vercel-related (titles/ids only):"
    op item list --vault "$VAULT" --format json \
      | python3 -c 'import json,sys
for it in json.load(sys.stdin):
    t=it.get("title","")
    if "vercel" in t.lower() or "hop" in t.lower():
        print(f"  {it.get(\"id\")}  {t}  [{it.get(\"category\")}]")'
    echo "# Then edit $TEMPLATE so each NAME=op://$VAULT/<item title>/<field> points at the right field."
    ;;

  template)
    [[ -f "$EXAMPLE" ]] || fail "missing $EXAMPLE"
    if [[ -f "$TEMPLATE" ]]; then
      echo "exists: $TEMPLATE (edit it; not overwriting)"
    else
      cp "$EXAMPLE" "$TEMPLATE"; chmod 600 "$TEMPLATE"
      echo "wrote $TEMPLATE — edit the op:// references (file is gitignored)"
    fi
    ;;

  ids)
    need vercel vercel-cli
    need jq jq
    # `vercel link` writes .vercel/project.json {orgId, projectId}; .vercel/ is gitignored.
    vercel link --yes --scope "$VERCEL_SCOPE" --project "$VERCEL_PROJECT" >/dev/null
    [[ -f .vercel/project.json ]] || fail ".vercel/project.json not written by vercel link"
    jq -r '.orgId'     .vercel/project.json | gh secret set VERCEL_ORG_ID     --repo "$REPO"
    jq -r '.projectId' .vercel/project.json | gh secret set VERCEL_PROJECT_ID --repo "$REPO"
    echo "OK set VERCEL_ORG_ID and VERCEL_PROJECT_ID on $REPO (values not shown)"
    ;;

  hook)
    need vercel vercel-cli
    need jq jq
    # Create (or reuse) the production deploy hook; store its URL in 1Password, then push to GitHub.
    hook_json="$(vercel deploy-hooks ls --scope "$VERCEL_SCOPE" --format json 2>/dev/null || echo '[]')"
    url="$(printf '%s' "$hook_json" | jq -r --arg n "$HOOK_NAME" '.[]? | select(.name==$n) | .url' | head -1)"
    if [[ -z "$url" || "$url" == "null" ]]; then
      vercel deploy-hooks create "$HOOK_NAME" --ref "$HOOK_REF" --scope "$VERCEL_SCOPE" >/dev/null
      hook_json="$(vercel deploy-hooks ls --scope "$VERCEL_SCOPE" --format json)"
      url="$(printf '%s' "$hook_json" | jq -r --arg n "$HOOK_NAME" '.[]? | select(.name==$n) | .url' | head -1)"
    fi
    [[ -n "$url" && "$url" != "null" ]] || fail "could not obtain deploy hook URL for $HOOK_NAME"
    tmpl="$(mktemp)"; trap 'rm -f "$tmpl"' EXIT
    printf '{"title":"Vercel deploy hook %s","category":"API_CREDENTIAL","fields":[{"id":"credential","type":"CONCEALED","label":"credential","value":%s},{"id":"hostname","type":"STRING","label":"hostname","value":"api.vercel.com"}]}\n' \
      "$HOOK_NAME" "$(printf '%s' "$url" | jq -R .)" > "$tmpl"
    op item create --vault "$VAULT" --template "$tmpl" >/dev/null
    printf '%s' "$url" | gh secret set VERCEL_DEPLOY_HOOK_PROD --repo "$REPO"
    echo "OK deploy hook '$HOOK_NAME' stored as op://$VAULT/Vercel deploy hook $HOOK_NAME/credential and pushed as VERCEL_DEPLOY_HOOK_PROD"
    ;;

  push)
    [[ -f "$TEMPLATE" ]] || fail "missing $TEMPLATE — run: $0 template"
    dry=0; [[ "${1:-}" == "--dry-run" ]] && dry=1
    if (( dry )); then
      echo "# dry-run: references only (no values resolved)"; grep -v '^\s*#' "$TEMPLATE" | sed 's/=.*op:\/\//=op:\/\//'
      exit 0
    fi
    tmp="$(mktemp)"; chmod 600 "$tmp"; trap 'rm -f "$tmp"' EXIT
    op inject -i "$TEMPLATE" -o "$tmp" -f >/dev/null
    # Refuse to push if any reference failed to resolve (op leaves them verbatim).
    if grep -q 'op://' "$tmp"; then
      grep -o '^[A-Z0-9_]*=op://[^ ]*' "$tmp" | sed 's/=.*//' | sed 's/^/unresolved: /' >&2
      fail "one or more op:// references did not resolve — check $TEMPLATE and vault '$VAULT'"
    fi
    gh secret set -f "$tmp" --repo "$REPO"
    echo "OK pushed $(grep -c '=' "$tmp") secret(s) to $REPO (values not shown)"
    ;;

  verify)
    echo "# gh secret list --repo $REPO"
    gh secret list --repo "$REPO"
    missing=()
    for n in "${NAMES[@]}"; do gh secret list --repo "$REPO" | grep -q "^$n" || missing+=("$n"); done
    if (( ${#missing[@]} )); then echo "MISSING: ${missing[*]}" >&2; exit 1; fi
    echo "OK all ${#NAMES[@]} names present: ${NAMES[*]}"
    ;;

  help|*)
    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
    ;;
esac
