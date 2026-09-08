# #142 — Ambient light + other sensors (honest availability)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/142

## Status

**Implemented on this branch.** `OtherSensorsGate` + `docs/ios-sensor-availability.md`. Ambient lux is **nil** (never faked).

## Goal

Inventory non-CoreMotion sensors with honest unavailable copy.

## Prior art

Web ambient-light is WebKit-limited (`docs/sensors-chrome-ios.md`). Apple has no public lux API for third-party apps. **Build** fail-closed table.

## Shipped on `main`

None for native ambient.

## Remaining scope

SensorKit ambient only after #148.

## Wire fields

Do **not** add lux. Altimeter optional via #140.

## Clamps / safety

No fake lux. Camera default out.

## Acceptance tests

`ambientLux()==nil`; ambient row available=false.

## CI gate

IoTASPSmoke + `tests/test_other_sensors.py`.

## Risks / HW limits

Claiming lux would be a lie on public iOS.

## Sources

Issue #142, `docs/ios-sensor-availability.md`.
