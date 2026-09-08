# #44 — Web PWA impulse-to-blast

## Status

Stubbed in `public/index.html`.

## Goal

Detect a best-effort motion or microphone-difference impulse and expose the resulting blast decision in telemetry.

## Prior art

Reuse existing sensor arming, `micDiff`, monitor logging, volume controls, and heartbeat transport.

## Shipped on `main`

No impulse-to-blast web path is shipped on `main`.

## Remaining scope

Tune thresholds from fixture traces and validate false-positive behavior on owned iPhones.

## Wire fields

Adds `impulse` and `volBlast` to schema-version-1 telemetry; see `docs/api-contract.md`.

## Clamps / safety

Blast volume is bounded by `VOL_PATCH_MAX`; Hold / Manual prevents triggering.

## Acceptance tests

The impulse flag remains latched until the next heartbeat snapshots it, then clears after acknowledgement.

## CI gate

`tests/test_public_html.py` checks the latch, heartbeat, and Hold behavior.

## Risks / HW limits

WebKit scheduling and permission availability limit detection timing and reliability.

## Sources

- `docs/algorithms.md`
- `docs/api-contract.md`
