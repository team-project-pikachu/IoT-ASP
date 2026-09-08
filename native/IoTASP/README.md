# IoT-ASP native — iPhone node + Watch + macOS command center

Xcode multi-target app for hop-ultrasonic / IoT-ASP control.

| Path | Role |
|------|------|
| `IoTASPApp/` | **iPhone node** — On/Off + status. Command center is not here. |
| `IoTASPWatch/` | **Apple Watch** companion (status + Hold) |
| `IoTASPCommand/` | **macOS command center** — WKWebView of the Vercel blaster |
| `Shared/` | Alarm state machine, impulse detector, fleet (Soundcore + Sonos), SensorKit gate |
| `Package.swift` | Shared logic + discoverable XCTest target (`swift test` when the selected toolchain includes XCTest) |
| `IoTASP.xcodeproj/` | Open in **Xcode.app** to build device/simulator |

Command center (SDD / C3): **https://hop-ultrasonic-1digital-design.vercel.app/** (`public/`). Scheme **IoTASPCommand** loads that URL on Mac.

## Issues

- Related: [#140](https://github.com/team-project-pikachu/IoT-ASP/issues/140) full CoreMotion suite
- Related: [#41](https://github.com/team-project-pikachu/IoT-ASP/issues/41) native iOS+Watch
- Related: [#42](https://github.com/team-project-pikachu/IoT-ASP/issues/42) impulse→blast / alarm
- Related: [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39) Sonos Beam Node 3
- Related: [#9](https://github.com/team-project-pikachu/IoT-ASP/issues/9) SensorKit research (closed; entitlement still parked)
- TODO Soundcore specs: [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43) → `docs/hardware/soundcore-2.md` (dossier: `soundcore-specs.md` / PR #55)


## What runs on-device vs stubbed

| Feature | On-device (with Xcode + device) | Stub / gated |
|---------|--------------------------------|--------------|
| Alarm state machine | Runs (unit-tested via SPM) | — |
| Impulse simulate button | Session API only (not on the phone UI) | Real CoreMotion wiring when On |
| Phone chrome | On / Off + status + Hold | Nest / Glass / Systems stay on the Vercel command center |
| On | Motion + 48 kHz mic + permission sequence | Backgrounding pauses sensing (#145) |
| CoreMotion 1–100 Hz | Code present (`PhoneMotionLogger` + `CoreMotionSuite`) | Simulator: availability all-false; pedometer skipped; mag/altimeter optional |
| AVRoutePicker / A2DP / AirPlay session | Runs on device | Needs full Xcode; CLT-only hosts cannot `xcodebuild` |
| watchOS UI + impulse/Hold | Runs on Watch simulator/device | WCSession mirror best-effort |
| SensorKit readers | Compile-time `#if canImport(SensorKit) && ASP_SENSORKIT_ENTITLED` | **Entitlement not granted** — always stub |
| SoCo / sonos-web | Out of process (LAN host) | Documented in `docs/sonos-beam.md` |
| Soundcore FR/power clamps | Honesty strings in `SoundcoreConstraints` | Official numbers TODO #43 |

## Build

```bash
# Shared tests (requires a Swift toolchain that includes XCTest)
cd native/IoTASP && swift test

# App / Watch (requires Xcode.app)
open IoTASP.xcodeproj
# Scheme: IoTASP (iPhone node) · IoTASPWatch · IoTASPCommand (macOS / Vercel)
```

Studio note: the installed Command Line Tools may omit XCTest, and `xcodebuild -version` fails when only
Command Line Tools are selected. In that environment, run `swift Scripts/alarm_smoke.swift`; install/select
Xcode.app before running `swift test` or building the app targets.

## Alarm reactivity (definition)

`armed → triggered → sustaining → cleared` (the next impulse retriggers directly)
Impulse (accel spike and/or micDiff onset, short rise) → `volBlast` jump to max (night/Hold rules) + shriek/extreme family preference. Clear only after **2.5 s** quiet hysteresis. Hold/Manual disarms.

## Skills

[skills-repo PR #1](https://github.com/team-project-pikachu/skills-repo/pull/1) `awesome-swift-ios` + SoCo/sonos-web priors.
