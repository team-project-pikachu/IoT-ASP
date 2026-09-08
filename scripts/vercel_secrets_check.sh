#!/usr/bin/env bash
# Local pre-flight: are the Vercel deploy secrets present in this shell? (names only — never values)
# Usage: bash scripts/vercel_secrets_check.sh
# Exit 0 when VERCEL_TOKEN, VERCEL_ORG_ID and VERCEL_PROJECT_ID are all set; 1 otherwise.
# See docs/deploy.md (issue #27). Values live in 1Password Environment "dev" and GitHub Actions secrets.
set -euo pipefail

REQUIRED=(VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID)
OPTIONAL=(VERCEL_DEPLOY_HOOK_PROD VERCEL_AUTOMATION_BYPASS_SECRET VERCEL_WEBHOOK_SECRET)

missing=0
echo "# required (Vercel CLI path)"
for name in "${REQUIRED[@]}"; do
  if [[ -n "${!name:+x}" ]]; then
    echo "${name}: set"
  else
    echo "${name}: MISSING"
    missing=$((missing + 1))
  fi
done
echo "# optional (deploy-hook fallback / preview protection bypass / webhooks #37)"
for name in "${OPTIONAL[@]}"; do
  if [[ -n "${!name:+x}" ]]; then
    echo "${name}: set"
  else
    echo "${name}: MISSING (optional)"
  fi
done

cat <<EOF

# ── Copy-paste recipe (item names, not values) ───────────────────────────────
# 1Password Environment "dev": read one value at a time (prints to the terminal — do not paste into chat/issues)
op read "op://dev/VERCEL_TOKEN/credential"
op read "op://dev/VERCEL_ORG_ID/credential"
op read "op://dev/VERCEL_PROJECT_ID/credential"
op read "op://dev/VERCEL_DEPLOY_HOOK_PROD/credential"
op read "op://dev/VERCEL_WEBHOOK_SECRET/credential"

# GitHub Actions secrets — the value is piped on stdin, never placed on the command line or echoed
op read "op://dev/VERCEL_TOKEN/credential"            | gh secret set VERCEL_TOKEN --repo team-project-pikachu/IoT-ASP
op read "op://dev/VERCEL_ORG_ID/credential"           | gh secret set VERCEL_ORG_ID --repo team-project-pikachu/IoT-ASP
op read "op://dev/VERCEL_PROJECT_ID/credential"       | gh secret set VERCEL_PROJECT_ID --repo team-project-pikachu/IoT-ASP
op read "op://dev/VERCEL_DEPLOY_HOOK_PROD/credential" | gh secret set VERCEL_DEPLOY_HOOK_PROD --repo team-project-pikachu/IoT-ASP
op read "op://dev/VERCEL_WEBHOOK_SECRET/credential"   | gh secret set VERCEL_WEBHOOK_SECRET --repo team-project-pikachu/IoT-ASP

# Automated alternative (written by the integrator): op inject → gh secret set -f
#   bash scripts/op_secrets_to_gh.sh
# Org/project ids: run \`vercel link\` in the repo and read .vercel/project.json (orgId, projectId) — gitignored.
# Webhooks (issue #37): docs/vercel-webhooks.md — HMAC verify via scripts/vercel_webhook_verify.py
EOF

if (( missing > 0 )); then
  echo "FAIL: ${missing} required Vercel secret name(s) missing from the environment (see docs/deploy.md, issue #27)" >&2
  exit 1
fi
echo "OK vercel_secrets_check"
