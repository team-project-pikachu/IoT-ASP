# #41 — CLT native compile-check evidence (PR #72)

**Date (UTC):** 2026-09-08T05:09:59Z
**Branch:** `feat/balanced-test-native-ci` (rebased onto `origin/main`)
**Honesty:** CLT smoke + SPM Shared library build only. No SensorKit entitlement, no Xcode.app app-scheme claim, no device lab.

## Procedure

1. `bash scripts/native_compile_check.sh`
2. `python3 -m pytest tests/test_native_compile_check.py tests/test_fleet_log.py -q`

## Observed results

### native_compile_check.sh

- **exit_code:** `0` → PASS
- stdout includes `alarm_smoke OK`, `OK swift build (IoTASPShared)`, `OK native_compile_check`
- `xcode-select=/Library/Developer/CommandLineTools` — app schemes NOT checked

### pytest

- **exit_code:** `0` → PASS (`71 passed` for fleet_log + native_compile_check)

## Pass/fail

| Check | Result |
|-------|--------|
| alarm_smoke.swift | PASS |
| swift package resolve + swift build Shared | PASS |
| fail gate on swift build errors (`set -e` + explicit fail) | PASS (present in script) |
| Xcode.app / SensorKit / App Store claim | N/A (explicitly not claimed) |
