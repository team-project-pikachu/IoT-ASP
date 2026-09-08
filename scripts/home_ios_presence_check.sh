#!/usr/bin/env bash
# M9 (#112) — ubuntu-safe presence check for native/IoTASPHome AppShell + build script.
# Does NOT run `swift build` (that is `make home-ios-build` on macOS / CLT).
# Failures are loud: missing files → exit 1 (no silent skip).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="${ROOT}/native/IoTASPHome"

fail() { echo "FAIL: $*" >&2; exit 1; }

require_file() { [[ -f "$1" ]] || fail "missing $1"; }

require_file "${ROOT}/scripts/home_ios_build.sh"
require_file "${PKG}/Package.swift"
require_file "${PKG}/Sources/HomeNestAlarm/AcousticEventClass.swift"
require_file "${PKG}/Sources/HomeNestAlarmUI/HomeNestRootView.swift"
require_file "${PKG}/Sources/AppShell/AppShellModule.swift"
require_file "${PKG}/Sources/AppShell/SensorKitShellModule.swift"
require_file "${PKG}/Sources/AppShell/CoreMotionShellModule.swift"
require_file "${PKG}/Sources/AppShell/MicAVFoundationShellModule.swift"
require_file "${PKG}/Sources/HomeNestAlarmUI/AppShellRootView.swift"
require_file "${PKG}/Resources/Info-AppShell.plist.example"
require_file "${ROOT}/docs/milestones/M9-native-ios-app-shell.md"

# Stub path must remain GoogleHomeSDK-optional (string gate — no proprietary SDK vendored).
if grep -Rql 'GoogleHomeSDK' "${PKG}/Sources" 2>/dev/null; then
  grep -Rql 'canImport(GoogleHomeSDK)' "${PKG}/Sources" \
    || fail "GoogleHomeSDK referenced without canImport stub gate"
fi

echo "OK home-ios-presence (M9 AppShell + M8 Nest stub files)"
