# ISSUE-41 — Native iOS + watchOS

**Status:** stub deepened (stack PR4) + CLT compile-check (stack PR5) — still no entitlement / App Store

## Did

- `native/IoTASP/` + SPM Shared library + CoreMotion session (from #40)
- `docs/native-xcode.md` build matrix
- `native/IoTASP/SYSTEMS-CHECK.md` printable checklist
- `scripts/native_compile_check.sh` + `make native-check` — `alarm_smoke.swift` + `swift package resolve` / best-effort `swift build` **without Xcode.app**
- `tests/test_native_compile_check.py`

## Didn't

- SensorKit entitlement · signed build · claim device lab complete · `xcodebuild` app schemes

## Next

- Owner Xcode.app session; tick SYSTEMS-CHECK
