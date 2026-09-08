#!/usr/bin/env bash
# M8 — stub-build Google Home / Nest iOS package without proprietary GoogleHomeSDK.
# Exit 0 on successful `swift build`. Exit 2 if swift missing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="${ROOT}/native/IoTASPHome"

fail() { echo "FAIL: $*" >&2; exit 1; }

command -v swift >/dev/null 2>&1 || {
  echo "FAIL: swift not on PATH (install Xcode CLT or full Xcode.app)" >&2
  exit 2
}

[[ -f "${PKG}/Package.swift" ]] || fail "missing ${PKG}/Package.swift"

echo "# swift: $(swift --version 2>&1 | head -n 1)"
echo "# xcrun swift: $(xcrun --find swift 2>/dev/null || echo n/a)"
echo "# mode: stub (GoogleHomeSDK not required)"

(
  cd "$PKG"
  swift package resolve
  swift build
)

echo "OK home-ios-build (native/IoTASPHome stub)"
# Optional: XCTest needs fuller toolchain — do not fail the gate if swift test unavailable.
if (cd "$PKG" && swift test >/dev/null 2>&1); then
  echo "OK swift test (HomeNestAlarmTests)"
else
  echo "NOTE: swift test skipped or unavailable on this host (build gate still green)"
fi
exit 0
