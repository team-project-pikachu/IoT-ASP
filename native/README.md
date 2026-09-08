# Native stubs (iOS + watchOS + Sonos shell)

Balanced stub-first landing for issues **#41 / #48 / #52** (native) and **#39** (Sonos AirPlay shell).

| Path | Role |
|------|------|
| [`IoTASP/`](IoTASP/) | Multi-target sketch: iPhone + Watch + shared alarm/impulse/fleet (Swift Package + `.xcodeproj`) |
| [`IoTASPHome/`](IoTASPHome/) | **M8 second feature:** Google Home / Nest + Gemini sound-burst + glass shatter (`make home-ios-build`, macOS) |
| [`ios-sonos-shell/`](ios-sonos-shell/) | Minimal `AVRoutePickerView` AirPlay shell for Beam Gen 2 research |

## Honesty

- **Not** a signed App Store build. SensorKit stays entitlement-gated (`#if` / capability stubs).
- Studio may only have Command Line Tools — `xcodebuild` needs full Xcode.app.
- Shared alarm logic smoke: `cd IoTASP && swift Scripts/alarm_smoke.swift`
- M8 Home/Nest stub gate (macOS): `bash scripts/home_ios_build.sh` or `make home-ios-build`
- Docs: [`docs/native-xcode.md`](../docs/native-xcode.md), [`docs/sonos-beam.md`](../docs/sonos-beam.md), [`docs/hardware/soundcore-specs.md`](../docs/hardware/soundcore-specs.md), [`docs/milestones/M8-nest-gemini-soundburst-mvp.md`](../docs/milestones/M8-nest-gemini-soundburst-mvp.md)
