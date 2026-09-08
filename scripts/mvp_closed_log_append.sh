#!/usr/bin/env bash
# Append closed-issue line(s) to docs/mvp-closed-log.md (local / CI helper).
#
#   bash scripts/mvp_closed_log_append.sh <issue_number> [outcome words…]
#   bash scripts/mvp_closed_log_append.sh --backfill
#
# Idempotent for the same #N. Backfill enumerates closed issues via
# `gh issue list --state closed` (paginated). Related: docs/mvp-roadmap.md, #65/#68.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="${ROOT}/docs/mvp-closed-log.md"
REPO="${REPO:-team-project-pikachu/IoT-ASP}"

fail() { echo "FAIL: $*" >&2; exit 1; }

append_one() {
  local N="$1"
  shift || true
  local OUTCOME="${*:-closed}"

  if [[ -z "${N}" || ! "${N}" =~ ^[0-9]+$ ]]; then
    fail "usage: $0 <issue_number> [outcome…]  |  $0 --backfill"
  fi

  if [[ ! -f "${LOG}" ]]; then
    fail "missing ${LOG}"
  fi

  if grep -F "| #${N} |" "${LOG}" >/dev/null 2>&1; then
    echo "already logged #${N}"
    return 0
  fi

  local TITLE=""
  if command -v gh >/dev/null 2>&1; then
    TITLE="$(gh issue view "${N}" -R "${REPO}" --json title --jq .title 2>/dev/null || true)"
  fi
  TITLE="${TITLE:-issue ${N}}"
  TITLE="$(printf '%s' "${TITLE}" | tr '|\n\r' ' /  ' | sed 's/  */ /g' | cut -c1-160)"
  OUTCOME="$(printf '%s' "${OUTCOME}" | tr '|\n\r' ' /  ' | sed 's/  */ /g' | cut -c1-200)"
  local DAY
  DAY="$(date -u +%Y-%m-%d)"
  local LINE="${DAY} | #${N} | ${TITLE} | ${OUTCOME}"
  printf '%s\n' "${LINE}" >> "${LOG}"
  echo "appended: ${LINE}"
}

backfill() {
  command -v gh >/dev/null 2>&1 || fail "gh CLI required for --backfill"
  echo "backfill: listing closed issues on ${REPO} (paginated)…"
  local nums n
  # Paginated REST — no silent 200-result cap from `gh issue list --limit`.
  nums="$(
    gh api --paginate "repos/${REPO}/issues?state=closed&per_page=100" \
      --jq '.[] | select(has("pull_request") | not) | .number' \
      | sort -n | uniq
  )"
  for n in ${nums}; do
    [[ -n "${n}" ]] || continue
    append_one "${n}" closed
  done
  echo "OK backfill"
}

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <issue_number> [outcome…]  |  $0 --backfill" >&2
  exit 2
fi

if [[ "$1" == "--backfill" ]]; then
  backfill
  exit 0
fi

append_one "$@"
echo "OK mvp_closed_log_append #$1"
