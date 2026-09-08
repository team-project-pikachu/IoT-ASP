# Native stubs (iOS + watchOS + Sonos shell)

Balanced stub-first landing for issues **#41 / #48 / #52** (native) and **#39** (Sonos AirPlay shell).

| Path | Role |
|------|------|
| [`IoTASP/`](IoTASP/) | Multi-target sketch: iPhone + Watch + shared alarm/impulse/fleet (Swift Package + `.xcodeproj`) |
| [`ios-sonos-shell/`](ios-sonos-shell/) | Minimal `AVRoutePickerView` AirPlay shell for Beam Gen 2 research |
| [`IoTASPSensorKit/`](IoTASPSensorKit/) | M9 SensorKit entitlement **stub** SPM (#110) — CI builds without Apple grant |

## Honesty

- **Not** a signed App Store build. SensorKit stays entitlement-gated (`#if` / capability stubs).
- Studio may only have Command Line Tools — `xcodebuild` needs full Xcode.app.
- Shared alarm logic smoke: `cd IoTASP && swift Scripts/alarm_smoke.swift`
- Repo gate (CLT): `bash scripts/native_compile_check.sh` or `make native-check`
- SensorKit stub gate: `make sensorkit-stub-build` (no entitlement / no secrets)
- Docs: [`docs/native-xcode.md`](../docs/native-xcode.md), [`docs/sonos-beam.md`](../docs/sonos-beam.md), [`docs/hardware/soundcore-specs.md`](../docs/hardware/soundcore-specs.md)
