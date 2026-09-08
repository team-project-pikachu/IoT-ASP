# #143 — SensorKit concrete SRSensorReader map

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/143

## Status

**Implemented on this branch.** `SensorKitReaderMap` lists requestable types. CI stub compiles without entitlement. CoreMotion remains primary.

## Goal

Concrete reader map vs entitlement-gated no-ops.

## Prior art

`SensorKitGate`; SpeziSensorKit (do not vendor); Apple SensorKit docs. **Build** enum map.

## Shipped on `main`

Compile-time stub only.

## Remaining scope

Flip `ASP_SENSORKIT_ENTITLED` only after #148 evidence.

## Wire fields

None.

## Clamps / safety

No invented grants. Visits skipped (PII).

## Acceptance tests

All specs require grant; start(false) mentions CoreMotion.

## CI gate

IoTASPSmoke + `tests/test_sensorkit_readers.py`.

## Risks / HW limits

Without Apple grant, readers never start.

## Sources

https://developer.apple.com/documentation/sensorkit
https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.sensorkit.reader.allow
Issue #143, #110, #148.
