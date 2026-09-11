#!/usr/bin/env bash
# Append a durable line to docs/mvp-closed-log.md when a GitHub issue is closed.
# Uses `gh` only; no secrets; never copies issue body text (PII-safe).
#
#   bash scripts/mvp_closed_log_append.sh <issue_number>
#   bash scripts/mvp_closed_log_append.sh --backfill
# Idempotent: skips if a table row for #N already exists.
# Optional Actions workflow may call this on issues:closed; if contents:write is
# denied by rulesets, document the manual path and prefer a PR branch.
# Related: #68, docs/mvp-roadmap.md (#69).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOG="${LOG:-docs/mvp-closed-log.md}"
# Append closed-issue line(s) to docs/mvp-closed-log.md (local / CI helper).
#   bash scripts/mvp_closed_log_append.sh <issue_number> [outcome words…]
# Idempotent for the same #N. Backfill enumerates closed issues via
# `gh issue list --state closed` (paginated). Related: docs/mvp-roadmap.md, #65/#68.
LOG="${ROOT}/docs/mvp-closed-log.md"
REPO="${REPO:-team-project-pikachu/IoT-ASP}"

fail() { echo "FAIL: $*" >&2; exit 1; }

command -v gh >/dev/null 2>&1 || fail "gh CLI required (https://cli.github.com/)"
gh auth status >/dev/null 2>&1 || fail "gh not authenticated — run 'gh auth login'"
[[ -f "$LOG" ]] || fail "missing $LOG — seed the file first"

# Truncate title for the markdown table cell.
trunc_title() {
  local t="$1"
  if (( ${#t} > 80 )); then
    printf '%s…' "${t:0:79}"
  else
    printf '%s' "$t"
  fi
}
# Return 0 if log already has a row for #N.
has_row() {
  local n="$1"
  grep -qE "\\|[[:space:]]*#[ ]?${n}[[:space:]]*\\|" "$LOG" 2>/dev/null
append_one() {
  if has_row "$n"; then
    echo "skip #$n (already in $LOG)"
    return 0
  # Fetch metadata only (title, labels, closed_at, state, closed_by when present).
  local json
  json="$(gh api "repos/$REPO/issues/$n" --jq '{number,title,state,closed_at,labels:[.labels[].name],closed_by:(.closed_by.login // "unknown")}')" \
    || fail "gh api repos/$REPO/issues/$n failed"
  local state title closed_at labels closer date
  state="$(printf '%s' "$json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"])')"
  [[ "$state" == "closed" ]] || fail "issue #$n is not closed (state=$state)"
  title="$(printf '%s' "$json" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("title") or "")')"
  closed_at="$(printf '%s' "$json" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("closed_at") or "")')"
  labels="$(printf '%s' "$json" | python3 -c 'import json,sys; labs=json.load(sys.stdin).get("labels") or []; print(", ".join(labs) if labs else "-")')"
  closer="$(printf '%s' "$json" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("closed_by") or "unknown")')"
  if [[ -n "$closed_at" ]]; then
    date="${closed_at:0:10}"
    date="$(date -u +%Y-%m-%d)"
  local tcell
  tcell="$(trunc_title "$title")"
  # Escape pipes in title for markdown table safety.
  tcell="${tcell//|/\\|}"
  local row="| ${date} | #${n} | ${tcell} | ${labels} | ${closer} |"
  # Insert after the table header separator line (second |---| row).
  python3 - "$LOG" "$row" <<'PY'
import sys
path, row = sys.argv[1], sys.argv[2]
lines = open(path, encoding="utf-8").read().splitlines(True)
out = []
inserted = False
sep_seen = 0
for line in lines:
    out.append(line)
    if line.lstrip().startswith("|---") or line.lstrip().startswith("| ---"):
        sep_seen += 1
        if sep_seen == 1 and not inserted:
            out.append(row + "\n")
            inserted = True
if not inserted:
    # Fallback: append at end
    if out and not out[-1].endswith("\n"):
        out[-1] += "\n"
    out.append(row + "\n")
open(path, "w", encoding="utf-8").writelines(out)
print("appended:", row)
PY
backfill() {
  echo "backfill: listing closed issues on $REPO (paginated)…"
  local nums n
  # Paginated retrieval — do not silently stop at 200 with a false OK.
  nums="$(
    gh api --paginate "repos/${REPO}/issues?state=closed&per_page=100" \
      --jq '.[] | select(has("pull_request") | not) | .number' \
      | sort -n | uniq
  )"
  for n in $nums; do
    [[ -n "$n" ]] || continue
    append_one "$n"
    append_one "$n" || true
  local N="$1"
  shift || true
  local OUTCOME="${*:-closed}"
  if [[ -z "${N}" || ! "${N}" =~ ^[0-9]+$ ]]; then
    fail "usage: $0 <issue_number> [outcome…]  |  $0 --backfill"
  if [[ ! -f "${LOG}" ]]; then
    fail "missing ${LOG}"
  if grep -F "| #${N} |" "${LOG}" >/dev/null 2>&1; then
    echo "already logged #${N}"
  local TITLE=""
  if command -v gh >/dev/null 2>&1; then
    TITLE="$(gh issue view "${N}" -R "${REPO}" --json title --jq .title 2>/dev/null || true)"
  TITLE="${TITLE:-issue ${N}}"
  TITLE="$(printf '%s' "${TITLE}" | tr '|\n\r' ' /  ' | sed 's/  */ /g' | cut -c1-160)"
  OUTCOME="$(printf '%s' "${OUTCOME}" | tr '|\n\r' ' /  ' | sed 's/  */ /g' | cut -c1-200)"
  local DAY
  DAY="$(date -u +%Y-%m-%d)"
  local LINE="${DAY} | #${N} | ${TITLE} | ${OUTCOME}"
  printf '%s\n' "${LINE}" >> "${LOG}"
  echo "appended: ${LINE}"
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
  echo "Usage: $0 <issue_number> | --backfill" >&2
  echo "Usage: $0 <issue_number> [outcome…]  |  $0 --backfill" >&2
  exit 2
fi

if [[ "$1" == "--backfill" ]]; then
  backfill
  exit 0
fi

[[ "$1" =~ ^[0-9]+$ ]] || fail "issue number must be digits, got: $1"
append_one "$1"
append_one "$@"
echo "OK mvp_closed_log_append #$1"
