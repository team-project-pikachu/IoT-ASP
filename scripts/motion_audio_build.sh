#!/usr/bin/env bash
# M9 / #111 — CoreMotion + AVFoundation (mic) stub SPM build (simulator/CI safe).
# Exit 0 on successful `swift build`. `swift test` when XCTest available.
# Exit 2 if swift missing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="${ROOT}/native/IoTASPMotionAudio"

fail() { echo "FAIL: $*" >&2; exit 1; }

command -v swift >/dev/null 2>&1 || {
  echo "FAIL: swift not on PATH (install Xcode CLT or full Xcode.app)" >&2
  exit 2
}

[[ -f "${PKG}/Package.swift" ]] || fail "missing ${PKG}/Package.swift"

echo "# swift: $(swift --version 2>&1 | head -n 1)"
echo "# mode: stub (device motion / mic HW not required)"

(
  cd "$PKG"
  swift package resolve
  swift build
)

echo "OK motion-audio-build (native/IoTASPMotionAudio stub)"

set +e
TEST_OUT="$(cd "$PKG" && swift test 2>&1)"
TEST_RC=$?
set -e
printf '%s\n' "$TEST_OUT"
if [[ "$TEST_RC" -eq 0 ]]; then
  echo "OK swift test (IoTASPMotionAudioTests)"
  exit 0
fi
if printf '%s\n' "$TEST_OUT" | grep -Fq "no such module 'XCTest'"; then
  echo "NOTE: XCTest unavailable on this host (CLT-only). Build gate remains green; run tests under full Xcode.app."
  exit 0
fi
fail "swift test failed (exit ${TEST_RC})"
