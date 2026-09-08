# #149 — Device capability matrix

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/149

## Status

**Implemented on this branch (docs).** Unknown cells marked unknown.

## Goal

Fleet matrix for 48 kHz, US band, CoreMotion, A2DP, Sonos, SensorKit.

## Prior art

README fleet 2× iPhone 16 + iPhone 14; `docs/iphone-bluetooth.md`; Soundcore honesty. **Build** table; do not invent on-device results.

## Shipped on `main`

Narrative fleet notes only.

## Remaining scope

Fill cells after #151 device runs.

## Wire fields

hwCaps parity — not a new schemaVersion.

## Clamps / safety

No fabricated pass/fail.

## Acceptance tests

Matrix file exists; contains `unknown`; SensorKit column is no.

## CI gate

`tests/test_device_matrix.py`.

## Risks / HW limits

A2DP codec may resample below Nyquist.

## Sources

Issue #149, `docs/ios-device-capability-matrix.md`.
