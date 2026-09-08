# #4 — Physical vib response (native CoreMotion)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/4 · Milestone: [iOS / iPhone](https://github.com/team-project-pikachu/IoT-ASP/milestone/10)

## Status

**Implemented on this branch (native).** `PhysicalVibChannel` classifies gravity-excluded accel in **g**, ≥300 ms debounce, shake (3× threshold, two samples ≤400 ms) → hop; every 4th shake → reseed event. Web remaining scope in `04-06-vibration-channels.md` is unchanged.

## Goal

Respond to **physical** vibration via linear accelerometer (phone body / mount). Prefer userAcceleration; tunable threshold; debounced shake → force hop / rotate seed.

## Prior art

Web DeviceMotion path in `public/index.html` (partly shipped). Native `ImpulseDetector.observeAccel`. Apple `CMDeviceMotion.userAcceleration`. **Build** native channel; do not duplicate web HTML in this PR.

## Shipped on `main`

Web EMA `accelMag` + vib pill. Native impulse onset only. No shake→hop / g-unit conversion on native.

## Remaining scope

Wire shakeReseed into hop scheduler when native TX lands. Web HTML remaining items stay in spec 04-06.

## Wire fields

`vibClass=physical`, `absA` in **g**. No schemaVersion bump.

## Clamps / safety

`thresholdG` clamped [0.01, 2.0] (backend `vibThreshold` range). Disarmed channel returns `.none`. Hold / Manual still wins at alarm layer.

## Acceptance tests

Below-threshold `.none`; `.physical` at 0.15 g with thr 0.1; debounce 100 ms suppresses; double 0.4 g within 50 ms → `.shakeHop`; `armed: false` → `.none`.

## CI gate

`IoTASPSmoke` + `tests/test_physical_vib.py`.

## Risks / HW limits

DeviceMotion ~50–100 Hz requested, not guaranteed. Shake hop is audible later than the shake (A2DP latency).

## Sources

- Issue #4, `docs/specs/04-06-vibration-channels.md`
- https://developer.apple.com/documentation/coremotion/cmdevicemotion/useracceleration
