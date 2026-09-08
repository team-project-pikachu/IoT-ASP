# #45 — Web PWA alarm reactivity

## Status

Stubbed in `public/index.html`.

## Goal

Expose armed, triggered, sustaining, and cleared states with quiet hysteresis and repeat-trigger support.

## Prior art

Reuse the burst quiet window, monitor UI, and native alarm semantics rather than adding a second policy.

## Shipped on `main`

No web alarm lifecycle is shipped on `main`.

## Remaining scope

Validate timing on backgrounded iOS browsers and persist state transitions in structured fleet logs.

## Wire fields

Uses `alarmState`, `impulse`, and `volBlast` from `docs/api-contract.md`.

## Clamps / safety

Hold / Manual clears the alarm and prevents remote or local retriggering until released.

## Acceptance tests

Quiet hysteresis transitions sustaining to observable cleared; a later impulse transitions cleared to triggered.

## CI gate

Static HTML tests and native shared-state XCTest enforce matching lifecycle behavior.

## Risks / HW limits

Browser timer throttling may delay quiet-state transitions while the page is backgrounded.

## Sources

- `docs/algorithms.md`
- `docs/api-contract.md`
