# #42 — Combined impulse-to-blast alarm

## Status

Stubbed in the PWA and native shared Swift logic.

## Goal

Combine acceleration and microphone-difference impulse signals into an observable alarm lifecycle and bounded blast command.

## Prior art

Reuse the existing `micDiff`, DeviceMotion, Hold / Manual, and volume-clamp paths documented in `docs/algorithms.md`.

## Shipped on `main`

No combined alarm state machine is shipped on `main`.

## Remaining scope

Calibrate thresholds from owned-device traces and integrate durable fleet event storage.

## Wire fields

Uses additive schema-version-1 fields `impulse`, `volBlast`, and `alarmState`; see `docs/api-contract.md`.

## Clamps / safety

Volume stays within the existing 0–100 UI clamp. Hold / Manual suppresses triggers and clears blast state.

## Acceptance tests

An impulse transitions armed/cleared to triggered, repeated activity sustains, and quiet hysteresis leaves cleared observable.

## CI gate

Python HTML assertions, Swift XCTest, and the standalone Swift smoke script cover both implementations.

## Risks / HW limits

Browser microphone and motion APIs are best-effort; no on-phone CFD or true infrasound capture is claimed.

## Sources

- `docs/algorithms.md`
- `docs/api-contract.md`
