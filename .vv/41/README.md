# V&V — native IoTASP (#41)

**Config item:** `native/IoTASP/Package.swift`, `native/IoTASP/IoTASP.xcodeproj/project.pbxproj`
**Date:** 2026-09-08 (UTC)
**Revision:** PR #57 revision containing this evidence

## Procedure

```bash
cd native/IoTASP
swift Scripts/alarm_smoke.swift
swift package describe --type json
swift test --quiet
cd ../..
plutil -lint native/IoTASP/IoTASP.xcodeproj/project.pbxproj \
  native/IoTASP/IoTASPWatch/Info.plist native/IoTASP/IoTASPApp/Info.plist
```

## Observed results

| Check | Exit | Result |
|-------|-----:|--------|
| Alarm smoke | 0 | `alarm_smoke OK`; clear remains observable and retriggers |
| Package description | 0 | `IoTASPSharedTests` discovered with target type `test` |
| `swift test --quiet` | 1 | Local Command Line Tools omit `XCTest`; full Xcode toolchain required |
| Project/plist syntax | 0 | project and both plists `OK` |
| Watch packaging inspection | 0 | watch-app product type plus `Embed Watch Content` copy phase present |

## Pass/fail

| Requirement | Status |
|-------------|--------|
| Shared state-machine behavior on CLT host | **PASS** |
| SwiftPM test-target discovery | **PASS** |
| Xcode project/plist syntax | **PASS** |
| XCTest execution on this host | **BLOCKED — XCTest absent from selected CLT** |
| Signed iOS/Watch build and device delivery | **PENDING — Xcode.app + owner signing/device** |

SensorKit entitlement remains intentionally absent; its implementation stays compile-time gated.
