# Native stubs (iOS + watchOS + Sonos shell)

Balanced stub-first landing for issues **#41 / #48 / #52** (native) and **#39** (Sonos AirPlay shell), plus **M8** HomeNestAlarm (#102) and **M9** AppShell (#109).

| Path | Role |
|------|------|
| [`IoTASP/`](IoTASP/) | Multi-target sketch: iPhone + Watch + shared alarm/impulse/fleet (Swift Package + `.xcodeproj`) |
| [`IoTASPHome/`](IoTASPHome/) | **M8 + M9:** Nest/Glass (`HomeNestRootView`) + SensorKit-ready **`AppShellRootView`** (`make home-ios-build`) |
| [`ios-sonos-shell/`](ios-sonos-shell/) | Minimal `AVRoutePickerView` AirPlay shell for Beam Gen 2 research |

## Honesty

- **Not** a signed App Store build. SensorKit stays entitlement-gated (`#if` / capability stubs).
- Studio may only have Command Line Tools — `xcodebuild` needs full Xcode.app.
- Shared alarm logic smoke: `cd IoTASP && swift Scripts/alarm_smoke.swift`
- Repo gate (CLT): `bash scripts/native_compile_check.sh` or `make native-check`
- M8/M9 Home stub gate: `bash scripts/home_ios_build.sh` or `make home-ios-build`
- Docs: [`docs/native-xcode.md`](../docs/native-xcode.md), [`docs/milestones/M8-nest-gemini-soundburst-mvp.md`](../docs/milestones/M8-nest-gemini-soundburst-mvp.md), [`docs/milestones/M9-native-ios-app-shell.md`](../docs/milestones/M9-native-ios-app-shell.md)
