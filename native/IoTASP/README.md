# IoT-ASP native — iOS + watchOS

Xcode multi-target app for hop-ultrasonic / IoT-ASP control.

| Path | Role |
|------|------|
| `IoTASPApp/` | **iPhone** primary shell (SwiftUI) |
| `IoTASPWatch/` | **Apple Watch** companion (Watch Connectivity) |
| `Shared/` | Alarm state machine, impulse detector, fleet (Soundcore + Sonos), SensorKit gate |
| `Package.swift` | Shared logic + unit tests (`swift test`) without Xcode.app |
| `IoTASP.xcodeproj/` | Open in **Xcode.app** to build device/simulator |

## Issues

- Related: [#41](https://github.com/team-project-pikachu/IoT-ASP/issues/41) native iOS+Watch
- Related: [#42](https://github.com/team-project-pikachu/IoT-ASP/issues/42) impulse→blast / alarm
- Related: [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39) Sonos Beam Node 3
- Related: [#9](https://github.com/team-project-pikachu/IoT-ASP/issues/9) SensorKit research (closed; entitlement still parked)
- TODO Soundcore specs: [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43) → `docs/hardware/soundcore-2.md`

## What runs on-device vs stubbed

| Feature | On-device (with Xcode + device) | Stub / gated |
|---------|--------------------------------|--------------|
| Alarm state machine | Runs (unit-tested via SPM) | — |
| Impulse simulate button | Runs | Real CoreMotion wiring: start in session when `motionArmed` |
| CoreMotion 1–100 Hz | Code present (`PhoneMotionLogger`) | Hook `onSample` → detector in next pass |
| AVRoutePicker / A2DP / AirPlay session | Runs on device | Needs full Xcode; CLT-only hosts cannot `xcodebuild` |
| watchOS UI + impulse/Hold | Runs on Watch simulator/device | WCSession mirror best-effort |
| SensorKit readers | Compile-time `#if canImport(SensorKit) && ASP_SENSORKIT_ENTITLED` | **Entitlement not granted** — always stub |
| SoCo / sonos-web | Out of process (LAN host) | Documented in `docs/sonos-beam.md` |
| Soundcore FR/power clamps | Honesty strings in `SoundcoreConstraints` | Official numbers TODO #43 |

## Build

```bash
# Shared tests (no Xcode.app required)
cd native/IoTASP && swift test

# App / Watch (requires Xcode.app)
open IoTASP.xcodeproj
# Scheme: IoTASP (iOS) · IoTASPWatch
```

Studio note: `xcodebuild -version` fails when only Command Line Tools are selected — install/select Xcode.app.

## Alarm reactivity (definition)

`armed → triggered → sustaining → cleared→re-arm`  
Impulse (accel spike and/or micDiff onset, short rise) → `volBlast` jump to max (night/Hold rules) + shriek/extreme family preference. Clear only after **2.5 s** quiet hysteresis. Hold/Manual disarms.

## Skills

[skills-repo PR #1](https://github.com/team-project-pikachu/skills-repo/pull/1) `awesome-swift-ios` + SoCo/sonos-web priors.
