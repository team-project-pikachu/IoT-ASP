#!/usr/bin/env bash
# Simulate ADK-only packaging: only iot_asp_autoroute on PYTHONPATH (no monorepo
# packages/ tree). Fails if timestore still needs parents[N] / packages path hacks.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG_SRC="$ROOT/services/autoroute-adk/iot_asp_autoroute"
fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -d "$PKG_SRC" ]] || fail "missing $PKG_SRC"
[[ -d "$PKG_SRC/algo_timestore" ]] || fail "missing vendored algo_timestore under agent package"
[[ -f "$PKG_SRC/timestore.py" ]] || fail "missing timestore.py"

# Guard: no monorepo sys.path / parents[N] hacks in executable adapter code.
# Double-quoted BRE so ['"] is safe; allow optional whitespace after import_module(.
if grep -nE "parents\\[[0-9]+\\]|sys\\.path\\.(insert|append)|importlib\\.import_module\\([[:space:]]*['\"]algo_timestore" \
  "$PKG_SRC/timestore.py"; then
  fail "timestore.py still uses monorepo path hacks (not ADK-safe)"
fi
if grep -nE '^[^#]*sys\.path' "$PKG_SRC/timestore.py"; then
  fail "timestore.py still mutates sys.path (not ADK-safe)"
fi

TMP="$(mktemp -d "${TMPDIR:-/tmp}/adk-layout-XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# Copy agent package only — mirrors what `adk deploy … iot_asp_autoroute` ships.
mkdir -p "$TMP"
cp -R "$PKG_SRC" "$TMP/iot_asp_autoroute"
# Ensure packages/ is absent from the simulated layout.
[[ ! -e "$TMP/packages" ]]

# Isolate from the repo tree: cwd outside ROOT, PYTHONPATH = temp only.
cd "$TMP"
PYTHONPATH="$TMP" python3 - <<'PY'
import importlib
import sys
from pathlib import Path

assert not any("packages/algo-timestore" in p for p in sys.path), sys.path
assert not any(Path(p).name == "packages" for p in sys.path if p), sys.path

from iot_asp_autoroute.timestore import (  # noqa: E402
    autoroute_telemetry_stamp,
    autoroute_timestore_prior,
)

# Relative subpackage must resolve without monorepo root.
mod = importlib.import_module("iot_asp_autoroute.algo_timestore")
assert mod.N_PARAMS >= 16, mod.N_PARAMS
assert mod.TIME_QUANTUM_S == 0.0006, mod.TIME_QUANTUM_S

prior = autoroute_timestore_prior()
assert prior["fitParams"] >= 16, prior
assert prior["quantumS"] == 0.0006, prior
assert prior.get("engine"), prior

stamp = autoroute_telemetry_stamp()
assert stamp.get("quantumS") == 0.0006, stamp
assert "streetAddress" not in stamp, stamp

print("OK adk_layout_import_smoke")
PY
