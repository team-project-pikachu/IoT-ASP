#!/usr/bin/env bash
# #63 — report whether main-protection ruleset is present/active (never applies changes).
# Requires: gh auth. Exit 0 if enforcement=active and name matches; 1 otherwise.
set -euo pipefail
REPO="${GITHUB_REPOSITORY:-team-project-pikachu/IoT-ASP}"
WANT_NAME="main-protection"
ERR_TMP="$(mktemp "${TMPDIR:-/tmp}/iot-asp-ruleset-status.XXXXXX")"
trap 'rm -f "$ERR_TMP"' EXIT

echo "# rulesets for $REPO (names + enforcement only)"
out="$(gh api "repos/$REPO/rulesets" --jq \
  '.[] | select(.name == "main-protection") | "id=\(.id) name=\(.name) enforcement=\(.enforcement)"' \
  2>"$ERR_TMP" || true)"

if [[ -z "$out" ]]; then
  echo "FAIL: ruleset name=${WANT_NAME} not found or gh error" >&2
  cat "$ERR_TMP" >&2 || true
  exit 1
fi
printf '%s\n' "$out"
if ! printf '%s\n' "$out" | grep -q 'enforcement=active'; then
  echo "FAIL: expected enforcement=active" >&2
  exit 1
fi
echo "OK gh_protect_main_status"
