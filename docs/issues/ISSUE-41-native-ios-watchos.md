# ISSUE-41 — Native iOS + watchOS

**Status:** stub deepened (stack PR4) — still no entitlement / App Store  
**V&V:** [`.vv/41/README.md`](../../.vv/41/README.md) — refreshed **2026-09-08T04:47:09Z UTC**

## Did

- `native/IoTASP/` + SPM library target + `.testTarget` (`Tests/AlarmStateMachineTests.swift`)
- CLT path verified: `swift build` exit 0 · `swift Scripts/alarm_smoke.swift` exit 0
- `docs/native-xcode.md` build matrix (CLT vs Xcode.app honesty)
- `native/IoTASP/SYSTEMS-CHECK.md` printable checklist (AirPlay = C1 exception)
- Soundcore honesty cites A3105 manual FR **70 Hz–20 kHz** (`FleetConfig.swift`)

## Didn't

- SensorKit entitlement · signed build · claim device lab complete
- `swift test` green on CLT-only Studio (XCTest requires Xcode.app — exit 1 recorded in `.vv/41`)

## Next

- Owner Xcode.app session: `swift test` + tick SYSTEMS-CHECK on real HW
