#!/usr/bin/env bash
# Append one closed-issue line to docs/mvp-closed-log.md (local / CI helper).
# Usage: bash scripts/mvp_closed_log_append.sh <issue_number> [outcome words…]
# Idempotent for the same #N. Related: docs/mvp-roadmap.md, issue #65.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="${ROOT}/docs/mvp-closed-log.md"
N="${1:-}"
shift || true
OUTCOME="${*:-closed}"

if [[ -z "${N}" || ! "${N}" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 <issue_number> [outcome…]" >&2
  exit 2
fi

if [[ ! -f "${LOG}" ]]; then
  echo "missing ${LOG}" >&2
  exit 1
fi

if grep -F "| #${N} |" "${LOG}" >/dev/null 2>&1; then
  echo "already logged #${N}"
  exit 0
fi

TITLE=""
if command -v gh >/dev/null 2>&1; then
  TITLE="$(gh issue view "${N}" -R team-project-pikachu/IoT-ASP --json title --jq .title 2>/dev/null || true)"
fi
TITLE="${TITLE:-issue ${N}}"
TITLE="$(printf '%s' "${TITLE}" | tr '|\n\r' ' /  ' | sed 's/  */ /g' | cut -c1-160)"
OUTCOME="$(printf '%s' "${OUTCOME}" | tr '|\n\r' ' /  ' | sed 's/  */ /g' | cut -c1-200)"
DAY="$(date -u +%Y-%m-%d)"
LINE="${DAY} | #${N} | ${TITLE} | ${OUTCOME}"
printf '%s\n' "${LINE}" >> "${LOG}"
echo "appended: ${LINE}"
