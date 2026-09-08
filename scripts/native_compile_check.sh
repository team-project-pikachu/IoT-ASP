#!/usr/bin/env bash
# #41 native compile-check without claiming Xcode.app / SensorKit / device lab.
# Works on macOS Command Line Tools hosts (this Studio default).
#
# Usage:
#   bash scripts/native_compile_check.sh
# Exit 0 on CLT smoke + SPM resolve + Shared library build.
# Exit 2 if `swift` is missing. Never invents signing secrets.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NATIVE="${ROOT}/native/IoTASP"
SMOKE="${NATIVE}/Scripts/alarm_smoke.swift"
OUT="${NATIVE}/.swift-build-check.out"
ERR="${NATIVE}/.swift-build-check.err"

fail() { echo "FAIL: $*" >&2; exit 1; }

command -v swift >/dev/null 2>&1 || {
  echo "FAIL: swift not on PATH (install Xcode CLT or full Xcode.app)" >&2
  exit 2
}

[[ -f "$SMOKE" ]] || fail "missing $SMOKE"
[[ -f "${NATIVE}/Package.swift" ]] || fail "missing Package.swift"

echo "# swift: $(swift --version 2>&1 | head -n 1)"
echo "# host: CLT-or-Xcode (xcodebuild intentionally not required for this gate)"

# 1) Alarm / impulse smoke (no XCTest — works without Xcode.app)
(
  cd "$NATIVE"
  swift Scripts/alarm_smoke.swift
)

# 2) SPM resolve + Shared library build — must fail the gate on build errors
(
  cd "$NATIVE"
  swift package resolve
  if ! swift build -c release >"$OUT" 2>"$ERR"; then
    echo "FAIL: swift build (IoTASPShared) failed — see ${ERR}" >&2
    head -n 40 "$ERR" >&2 || true
    exit 1
  fi
  echo "OK swift build (IoTASPShared)"
)

# 3) Honesty: do not claim app-scheme compile without Xcode.app
XCODE_PATH="$(xcode-select -p 2>/dev/null || true)"
if [[ "$XCODE_PATH" == *CommandLineTools* ]] || [[ ! -d /Applications/Xcode.app ]]; then
  echo "# xcode-select=${XCODE_PATH:-unknown} — app schemes NOT checked"
else
  echo "# Xcode.app available — owner may run: open native/IoTASP/IoTASP.xcodeproj"
fi

echo "OK native_compile_check (CLT smoke; no SensorKit / App Store claim)"
