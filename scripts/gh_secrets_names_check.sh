#!/usr/bin/env bash
# #27 — report which Vercel Actions secret NAMES exist (never print values).
# Requires: gh auth. Exit 0 if required trio present; 1 if any required missing.
# Exit non-zero if `gh secret list` itself fails (auth/network/missing binary).
set -euo pipefail
REPO="${GITHUB_REPOSITORY:-team-project-pikachu/IoT-ASP}"
REQUIRED="VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID"
OPTIONAL="VERCEL_DEPLOY_HOOK_PROD VERCEL_AUTOMATION_BYPASS_SECRET VERCEL_WEBHOOK_SECRET"

echo "# gh secret list — names only ($REPO)"
# Do not swallow failures: missing auth / network / gh must surface as check failure.
LIST_OUT="$(gh secret list --repo "$REPO")"
NAMES="$(printf '%s\n' "$LIST_OUT" | awk 'NR==1 && /NAME/ {next} {print $1}')"

has() {
  local want="$1"
  echo "$NAMES" | awk -v w="$want" '$1==w {found=1} END{exit !found}'
}

missing=0
echo "# required"
for name in $REQUIRED; do
  if has "$name"; then echo "$name: PRESENT"; else echo "$name: MISSING"; missing=$((missing+1)); fi
done
echo "# optional"
for name in $OPTIONAL; do
  if has "$name"; then echo "$name: PRESENT"; else echo "$name: MISSING (optional)"; fi
done

cat <<'EOF'

# Owner recipe (names → 1Password Environment "dev" references only; stdin-safe)
#   op read "op://dev/VERCEL_TOKEN/credential" | gh secret set VERCEL_TOKEN --repo team-project-pikachu/IoT-ASP
#   op read "op://dev/VERCEL_ORG_ID/credential" | gh secret set VERCEL_ORG_ID --repo team-project-pikachu/IoT-ASP
#   op read "op://dev/VERCEL_PROJECT_ID/credential" | gh secret set VERCEL_PROJECT_ID --repo team-project-pikachu/IoT-ASP
# See docs/deploy.md §c and scripts/vercel_secrets_check.sh (local env) / .vv/deploy/VERCEL.md
EOF

if [ "$missing" -gt 0 ]; then
  echo "FAIL: ${missing} required secret name(s) not in GitHub Actions (issue #27)" >&2
  exit 1
fi
echo "OK gh_secrets_names_check"
