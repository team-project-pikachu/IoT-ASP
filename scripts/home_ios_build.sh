#!/usr/bin/env bash
# M8/M9 — stub-build Google Home / Nest + AppShell without proprietary GoogleHomeSDK.
# Exit 0 on successful `swift build`. `swift test` is required when XCTest is available;
# CLT-only hosts without XCTest get a NOTE (not a silent swallow of real failures).
# Exit 2 if swift missing.
# Failures surface clearly (no silent skip of missing Package.swift / M9 shell sources).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="${ROOT}/native/IoTASPHome"

fail() { echo "FAIL: $*" >&2; exit 1; }

command -v swift >/dev/null 2>&1 || {
  echo "FAIL: swift not on PATH (install Xcode CLT or full Xcode.app)" >&2
  exit 2
}

[[ -f "${PKG}/Package.swift" ]] || fail "missing ${PKG}/Package.swift"

# M9 (#109 / #112) — AppShell successor must be present; do not silently skip.
require_file() { [[ -f "$1" ]] || fail "missing required file: $1"; }
require_file "${PKG}/Sources/AppShell/AppShellModule.swift"
require_file "${PKG}/Sources/AppShell/SensorKitShellModule.swift"
require_file "${PKG}/Sources/AppShell/CoreMotionShellModule.swift"
require_file "${PKG}/Sources/AppShell/MicAVFoundationShellModule.swift"
require_file "${PKG}/Sources/HomeNestAlarmUI/AppShellRootView.swift"
require_file "${PKG}/Resources/Info-AppShell.plist.example"

echo "# swift: $(swift --version 2>&1 | head -n 1)"
echo "# xcrun swift: $(xcrun --find swift 2>/dev/null || echo n/a)"
echo "# mode: stub (GoogleHomeSDK not required; M9 AppShell presence checked)"

(
  cd "$PKG"
  swift package resolve
  swift build
)

echo "OK home-ios-build (native/IoTASPHome stub + M9 AppShell)"

set +e
TEST_OUT="$(cd "$PKG" && swift test 2>&1)"
TEST_RC=$?
set -e
printf '%s\n' "$TEST_OUT"
if [[ "$TEST_RC" -eq 0 ]]; then
  echo "OK swift test (HomeNestAlarmTests)"
  exit 0
fi
if printf '%s\n' "$TEST_OUT" | grep -Fq "no such module 'XCTest'"; then
  echo "NOTE: XCTest unavailable on this host (CLT-only). Build gate remains green; run tests under full Xcode.app."
  exit 0
fi
fail "swift test failed (exit ${TEST_RC})"
