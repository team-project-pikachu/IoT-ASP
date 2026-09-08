# V&V — native IoTASP Shared package (#41 / #39 / #43)

**Config item:** `native/IoTASP/Package.swift` (`.testTarget` `IoTASPSharedTests`) + Shared sources + `Scripts/alarm_smoke.swift` + `IoTASP.xcodeproj/project.pbxproj`  
**Docs:** `docs/native-xcode.md`, `native/IoTASP/SYSTEMS-CHECK.md`, `docs/sonos-beam.md`, `docs/hardware/soundcore-2.md`  
**Date:** 2026-09-08T04:47:09Z (UTC)  
**Revision:** branch `feat/balanced-native-hw-research` @ evidence capture (post–review fix; commit SHA recorded in this PR)  
**Host:** macOS CLT-only (`xcode-select -p` → `/Library/Developer/CommandLineTools`); no Xcode.app selected

## Procedure

```bash
cd native/IoTASP
swift build
swift Scripts/alarm_smoke.swift
swift package describe --type json
swift test   # expected fail on CLT (no XCTest module)
cd ../..
plutil -lint native/IoTASP/IoTASP.xcodeproj/project.pbxproj \
  native/IoTASP/IoTASPWatch/Info.plist native/IoTASP/IoTASPApp/Info.plist
```

## Observed results

| Command | Exit | Result | Notes |
|---------|------|--------|-------|
| `swift build` | **0** | **pass** | `IoTASPShared` compiles (`FleetConfig`, alarm, impulse) |
| `swift Scripts/alarm_smoke.swift` | **0** | **pass** | stdout `alarm_smoke OK` — CLT substitute for XCTest |
| `swift package describe --type json` | **0** | **pass** | `IoTASPSharedTests` discovered with target type `test` |
| `swift test` | **1** | **fail (expected on CLT)** | `error: no such module 'XCTest'` — package declares `.testTarget` for Xcode.app hosts |
| Project/plist syntax (`plutil -lint`) | **0** | **pass** | project and both plists `OK`; watch-app product type + Embed Watch Content present |
| SensorKit entitlement | n/a | **fail / not granted** | stub only; no entitlement in repo |
| Signed App Store / TestFlight | n/a | **not claimed** | |
| Soundcore A3105 published FR | n/a | **pass (docs)** | Manual band **70 Hz–20 kHz** cited in honesty string; 17–23 kHz at/above ceiling — not a lab FR curve |
| AirPlay / Beam as C1 carrier | n/a | **fail / exception** | Explicitly labeled non-C1 in `SYSTEMS-CHECK.md` |
| Device lab (3 phones + speakers) | n/a | **not run** | HW systems check remains owner-gated |

## Pass / fail summary

| Gate | Status |
|------|--------|
| Shared SPM compile (`swift build`) on CLT | **pass** |
| Alarm smoke assertions on CLT | **pass** |
| SwiftPM test-target discovery | **pass** |
| Xcode project/plist syntax | **pass** |
| XCTest via `swift test` on this Studio (CLT) | **fail (expected)** — requires Xcode.app |
| Signed iOS/Watch build and device delivery | **PENDING — Xcode.app + owner signing/device** |
| HW / entitlement / App Store claims | **fail / not claimed** |

## Honesty

- Do not treat CLT `swift build` as full XCTest coverage.
- Do not claim Soundcore flat response in 17–23 kHz; published manual ceiling is 20 kHz.
- Do not claim AirPlay Beam is C1-compliant carrier TX.

SensorKit entitlement remains intentionally absent; its implementation stays compile-time gated.
