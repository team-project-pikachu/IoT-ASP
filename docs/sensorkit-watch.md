# SensorKit + Watch + iPhone vib logging (#9 / #41)

**Honesty:** Safari / Chrome iOS **cannot** use SensorKit. Web stays DeviceMotion + mic. Full SensorKit needs a **native iOS app** + Apple research entitlement `com.apple.developer.sensorkit.reader.allow` — **not granted** in this wave (do not invent approval).

**Primary path:** iPhone native shell [`native/IoTASP/`](../native/IoTASP/) (`IoTASP` target).  
**Companion:** watchOS (`IoTASPWatch`) — on-wrist impulse / alarm mirror via Watch Connectivity.  
**Research freeze:** [sensorkit-research-closeout.md](sensorkit-research-closeout.md).

## Bands

| Band | Role |
|------|------|
| **1–100 Hz** | Log accel + gyro (CoreMotion device motion) on iPhone (+ Watch when available) |
| **10–20 Hz** | **Intense vibrations** band — TX gated (`lfDriveCapable`) and/or sensing priority aligned with `infra_felt` / LF gate (C6) |

## SensorKit (when entitled)

Apple index: https://developer.apple.com/documentation/sensorkit  

Relevant symbols for vib (names from docs scrape): `SRAccelerometerSensor`, `SRRotationRateSensor`, plus ambient / usage sensors as study design allows. Gate in code: `#if canImport(SensorKit) && ASP_SENSORKIT_ENTITLED` — see `Shared/Sensors/SensorKitGate.swift`. Entitlements file leaves SensorKit keys **commented**.

## Impulse → blast / alarm

See [algorithms.md](algorithms.md) § Impulse → blast / alarm reactivity. Telemetry: `impulse`, `volBlast`, `alarmState`. Hold/Manual wins.

## Fleet sinks in the app

| Node | Sink | Notes |
|------|------|-------|
| 1–2 | Soundcore 2 A2DP | First-class; manufacturer FR TODO [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43) → [hardware/soundcore-2.md](hardware/soundcore-2.md) |
| 3 | Sonos Beam Gen 2 AirPlay | [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39) · [sonos-beam.md](sonos-beam.md) |

LAN volume/group for Sonos: SoCo CLI / sonos-web (not a SensorKit substitute).

## Skills

[skills-repo PR #1](https://github.com/team-project-pikachu/skills-repo/pull/1) (`awesome-swift-ios`).
