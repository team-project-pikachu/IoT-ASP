#!/usr/bin/env bash
# Apply .github/rulesets/main-protection.json to the repo via the GitHub REST API (gh CLI).
#
#   bash scripts/gh_protect_main.sh              # apply to team-project-pikachu/IoT-ASP
#   REPO=owner/name bash scripts/gh_protect_main.sh
#   DRY_RUN=1 bash scripts/gh_protect_main.sh    # validate JSON + print the plan, no gh calls
#
# Idempotent: creates the ruleset when absent (POST), updates it in place when a ruleset with the
# same name exists (PUT). Then enables repo auto-merge + delete-branch-on-merge. No secrets are
# read or printed; auth comes from `gh auth login` (token stays inside gh's keyring).
# Docs: docs/branch-protection.md. Issue: #27.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REPO="${REPO:-team-project-pikachu/IoT-ASP}"
RULESET_FILE="${RULESET_FILE:-.github/rulesets/main-protection.json}"
DRY_RUN="${DRY_RUN:-0}"

fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -f "$RULESET_FILE" ]] || fail "missing $RULESET_FILE"

# Name comes from the JSON so the file stays the single source of truth.
NAME="$(python3 - "$RULESET_FILE" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
for key in ("name", "target", "enforcement", "conditions", "rules"):
    if key not in data:
        raise SystemExit(f"FAIL: {sys.argv[1]} missing key {key!r}")
if data["enforcement"] != "active":
    raise SystemExit(f"FAIL: enforcement must be 'active', got {data['enforcement']!r}")
print(data["name"])
PY
)"
[[ -n "$NAME" ]] || fail "could not read ruleset name from $RULESET_FILE"

echo "repo:    $REPO"
echo "ruleset: $NAME ($RULESET_FILE)"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY_RUN=1 — plan only:"
  echo "  gh auth status"
  echo "  gh api repos/$REPO/rulesets --jq '.[] | select(.name == \"$NAME\") | .id'"
  echo "  gh api -X PUT repos/$REPO/rulesets/<id> --input $RULESET_FILE   # if id found"
  echo "  gh api -X POST repos/$REPO/rulesets --input $RULESET_FILE       # else"
  echo "  gh api repos/$REPO/rulesets"
  echo "  gh api -X PATCH repos/$REPO -F allow_auto_merge=true -F delete_branch_on_merge=true"
  echo "OK gh_protect_main (dry-run)"
  exit 0
fi

command -v gh >/dev/null 2>&1 || fail "gh CLI not found — install https://cli.github.com/ and run 'gh auth login'"
gh auth status >/dev/null 2>&1 || fail "gh is not authenticated — run 'gh auth login' (scope: repo, admin on $REPO)"

# Look up an existing ruleset with the same name (repo-level rulesets only; org rulesets are
# reported with source_type=Organization and must not be overwritten from here).
# Errors (403 no admin, 404 wrong REPO, expired token) must surface, not be swallowed.
EXISTING_ID="$(gh api "repos/$REPO/rulesets" \
  --jq ".[] | select(.name == \"$NAME\" and .source_type == \"Repository\") | .id" | head -n 1)"

if [[ -n "$EXISTING_ID" ]]; then
  echo "updating existing ruleset id=$EXISTING_ID (PUT)"
  gh api -X PUT "repos/$REPO/rulesets/$EXISTING_ID" --input "$RULESET_FILE" \
    --jq '"ruleset \(.id) \(.name) enforcement=\(.enforcement)"'
else
  echo "creating ruleset (POST)"
  gh api -X POST "repos/$REPO/rulesets" --input "$RULESET_FILE" \
    --jq '"ruleset \(.id) \(.name) enforcement=\(.enforcement)"'
fi

echo "rulesets on $REPO:"
gh api "repos/$REPO/rulesets" --jq '.[] | "  \(.id)\t\(.name)\t\(.enforcement)\t\(.source_type)"'

echo "enabling auto-merge + delete-branch-on-merge on $REPO"
gh api -X PATCH "repos/$REPO" -F allow_auto_merge=true -F delete_branch_on_merge=true \
  --jq '"  allow_auto_merge=\(.allow_auto_merge) delete_branch_on_merge=\(.delete_branch_on_merge)"'

echo "OK gh_protect_main"
