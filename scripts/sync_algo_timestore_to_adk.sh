#!/usr/bin/env bash
# Sync canonical packages/algo-timestore → ADK-vendored subpackage.
# Canonical: packages/algo-timestore/algo_timestore/
# Vendor:    services/autoroute-adk/iot_asp_autoroute/algo_timestore/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/packages/algo-timestore/algo_timestore"
DST="$ROOT/services/autoroute-adk/iot_asp_autoroute/algo_timestore"
MODE="${1:-sync}"

fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -d "$SRC" ]] || fail "missing canonical source $SRC"

list_py() {
  # Exclude __pycache__ at any depth (nested packages create nested caches).
  (cd "$1" && find . -type f -name '*.py' ! -path '*/__pycache__/*' | LC_ALL=C sort)
}

check_sync() {
  [[ -d "$DST" ]] || fail "missing vendor copy $DST (run without --check)"
  local src_list dst_list
  src_list="$(list_py "$SRC")"
  dst_list="$(list_py "$DST")"
  if [[ "$src_list" != "$dst_list" ]]; then
    echo "FAIL: Python file set differs between canonical and vendor" >&2
    echo "--- canonical ---" >&2
    echo "$src_list" >&2
    echo "--- vendor ---" >&2
    echo "$dst_list" >&2
    exit 1
  fi
  local f
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    if ! diff -q "$SRC/$f" "$DST/$f" >/dev/null; then
      fail "drift in $f — run: bash scripts/sync_algo_timestore_to_adk.sh"
    fi
  done <<<"$src_list"
  echo "OK algo_timestore vendor in sync with packages/algo-timestore"
}

do_sync() {
  mkdir -p "$DST"
  local f
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    mkdir -p "$(dirname "$DST/$f")"
    cp "$SRC/$f" "$DST/$f"
  done < <(list_py "$SRC")
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    if [[ ! -f "$SRC/$f" ]]; then
      rm -f "$DST/$f"
    fi
  done < <(list_py "$DST")
  cat >"$DST/VENDOR.md" <<'EOF'
# Vendored for ADK packaging.

Canonical source: `packages/algo-timestore/algo_timestore/`

- Sync: `bash scripts/sync_algo_timestore_to_adk.sh`
- Verify: `bash scripts/sync_algo_timestore_to_adk.sh --check`

`adk deploy … iot_asp_autoroute` only ships this agent package; the monorepo
`packages/` tree is not included.
EOF
  echo "OK synced algo_timestore → $DST"
  check_sync
}

case "$MODE" in
  sync|"") do_sync ;;
  --check|check) check_sync ;;
  -h|--help)
    echo "usage: $0 [--check]"
    exit 0
    ;;
  *) fail "unknown mode: $MODE (use --check or omit for sync)" ;;
esac
