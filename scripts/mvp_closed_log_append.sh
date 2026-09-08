#!/usr/bin/env bash
# Append or backfill docs/mvp-closed-log.md from gh issue metadata (no bodies).
# Usage:
#   bash scripts/mvp_closed_log_append.sh <issue-number>
#   bash scripts/mvp_closed_log_append.sh --backfill
# Append closed-issue line(s) to docs/mvp-closed-log.md (local / CI helper).
#
#   bash scripts/mvp_closed_log_append.sh <issue_number> [outcome words…]
# Idempotent for the same #N. Backfill enumerates closed issues via
# `gh issue list --state closed` (paginated). Related: docs/mvp-roadmap.md, #65/#68.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="${ROOT}/docs/mvp-closed-log.md"
REPO="${GITHUB_REPOSITORY:-team-project-pikachu/IoT-ASP}"

if [[ ! -f "$LOG" ]]; then
  echo "missing $LOG" >&2
  exit 2
fi

# Encode pipe characters so Markdown table cells stay intact.
md_cell() {
  local s="$1"
  # Replace | with / — Markdown has no real cell escape; backslash-pipe still splits tables.
  s="${s//|//}"
  printf '%s' "$s"
}
row_for() {
  local num="$1"
  local tsv
  tsv="$(
    gh issue view "$num" -R "$REPO" --json number,title,closedAt,labels,milestone,state,stateReason \
      --jq '
        select(.state=="CLOSED") |
        [
          (.closedAt // "")[0:10],
          ("#" + (.number|tostring)),
          .title,
          ((.milestone.title) // "-"),
          (if (.labels|length)==0 then "-" else "`" + ([.labels[].name] | join(",")) + "`" end),
          (.stateReason // "-")
        ] | @tsv
      '
  )"
  [[ -n "$tsv" ]] || return 1
  local d n title mile labels reason
  IFS=$'\t' read -r d n title mile labels reason <<<"$tsv"
  printf '| %s | %s | %s | %s | %s | %s |\n' \
    "$(md_cell "$d")" \
    "$(md_cell "$n")" \
    "$(md_cell "$title")" \
    "$(md_cell "$mile")" \
    "$(md_cell "$labels")" \
    "$(md_cell "$reason")"
}
header_block() {
  cat <<'EOF'
# MVP closed-issue log
Append-only audit of **closed** GitHub issues for IoT-ASP.
Maintained by `scripts/mvp_closed_log_append.sh` ([#68](https://github.com/team-project-pikachu/IoT-ASP/issues/68)).
Optional Action: `.github/workflows/mvp-closed-log.yml` (PR branch under rulesets; optional MVP_CLOSED_LOG_PUSH_MAIN=1).
Do **not** paste issue bodies (may contain operator notes). Titles + metadata only.
| Closed (UTC) | Issue | Title | Milestone | Labels | Reason |
|--------------|------:|-------|-----------|--------|--------|
EOF
if [[ "${1:-}" == "--backfill" ]]; then
  tmp="$(mktemp)"
  header_block >"$tmp"
  while IFS=$'\t' read -r d n title mile labels reason; do
    printf '| %s | %s | %s | %s | %s | %s |\n' \
      "$(md_cell "$d")" \
      "$(md_cell "$n")" \
      "$(md_cell "$title")" \
      "$(md_cell "$mile")" \
      "$(md_cell "$labels")" \
      "$(md_cell "$reason")"
  done < <(
    gh issue list -R "$REPO" --state closed --limit 200 \
      --json number,title,closedAt,labels,milestone,stateReason \
      --jq 'sort_by(.closedAt)[] |
        [
          (.closedAt // "")[0:10],
          ("#" + (.number|tostring)),
          .title,
          ((.milestone.title) // "-"),
          (if (.labels|length)==0 then "-" else "`" + ([.labels[].name] | join(",")) + "`" end),
          (.stateReason // "-")
        ] | @tsv'
  ) >>"$tmp"
  gh issue list -R "$REPO" --state closed --limit 200 \
    --json number,title,closedAt,labels,milestone,stateReason \
    --jq 'sort_by(.closedAt)[] |
      ] | @tsv' \
    | awk -F'\t' '{printf "| %s | %s | %s | %s | %s | %s |\n", $1, $2, $3, $4, $5, $6}' >>"$tmp"
  cat >>"$tmp" <<'EOF'
## Backfill / append
```bash
# Single issue (after close)
bash scripts/mvp_closed_log_append.sh 37
# Rebuild table body from all closed issues (keeps header)
bash scripts/mvp_closed_log_append.sh --backfill
```
  mv "$tmp" "$LOG"
  echo "backfilled $LOG"
  exit 0
NUM="${1:?usage: mvp_closed_log_append.sh <issue-number>|--backfill}"
ROW="$(row_for "$NUM")"
if [[ -z "$ROW" ]]; then
  echo "issue #$NUM is not CLOSED or not found" >&2
  exit 1
if grep -qE "\| #${NUM} \|" "$LOG"; then
  echo "already logged #$NUM"
  exit 0
fi

# Insert as the last Markdown table row: discard blank lines immediately
# before ## Backfill, print the new row, then a blank, then the heading.
# Insert before the ## Backfill section if present; else append.
if grep -q '^## Backfill' "$LOG"; then
  awk -v row="$ROW" '
    /^## Backfill/ && !done {
      print row
      print ""
      print
      done=1
      hold=""
      next
    }
    /^[[:space:]]*$/ && !done {
      hold = hold $0 ORS
      next
    }
    {
      if (hold != "") { printf "%s", hold; hold="" }
      print
    }
    END {
      if (hold != "" && !done) printf "%s", hold
      if (!done) print row
    }
  ' "$LOG" >"$tmp"
else
  printf '%s\n' "$ROW" >>"$LOG"
echo "appended #$NUM"
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
  if grep -F "| #${N} |" "${LOG}" >/dev/null 2>&1; then
    echo "already logged #${N}"
    return 0
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
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <issue_number> [outcome…]  |  $0 --backfill" >&2
if [[ "$1" == "--backfill" ]]; then
  backfill
append_one "$@"
echo "OK mvp_closed_log_append #$1"
