# #140 — CoreMotion suite evidence

**Date (UTC):** 2026-09-08
**Branch:** `feat/140-coremotion-suite`
**Subject:** `native/IoTASP` @ this revision
**Honesty:** CLT smoke + SPM Shared library + `IoTASPSmoke`. No SensorKit entitlement, no Xcode.app app-scheme claim, no device lab.

## Procedure

1. `bash scripts/native_compile_check.sh`
2. `python3 -m pytest tests/test_coremotion_suite.py tests/test_native_compile_check.py -q`

## Observed results

### native_compile_check.sh

- **exit_code:** `0` → PASS
- stdout includes `alarm_smoke OK`, `OK swift build (IoTASPShared)`, `IoTASPSmoke OK`, `OK native_compile_check`
- `xcode-select=/Library/Developer/CommandLineTools` — app schemes NOT checked

### IoTASPSmoke (#140)

- hz clamp 0.1 → 1, 400 → 100, NaN → 50
- pedometer `.skip`; accel/gyro/deviceMotion `.fleetVib`; mag/altimeter `.optional`
- simulator plan `armsAnything == false`
- `FullMotionSample` absA 0.5 for (0.3, -0.4, 0)
- Hold / Manual still clears alarm

### pytest

- **exit_code:** `0` → PASS (`6 passed`)

## Pass/fail

| Check | Result |
|-------|--------|
| CoreMotionSuite Foundation models | PASS |
| Pedometer never in product-use fleetVib | PASS |
| Simulator-safe availability all-false | PASS |
| PhoneMotionLogger iOS-only (SPM exclude) | PASS |
| Xcode.app / SensorKit / App Store claim | N/A (explicitly not claimed) |
