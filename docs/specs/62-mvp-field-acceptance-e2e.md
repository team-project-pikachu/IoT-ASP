# #62 — MVP field acceptance + Playwright e2e

## Status

Checklist + local Playwright smoke documented; field lab owner-gated; e2e not yet a required Actions check.

## Goal

Prove the three-phone Soundcore fleet path (including suddenFreq, night curve honesty, and Soundcore roll-off warning) and optionally promote Playwright smoke.

## Prior art

Reuse `tests/e2e/` and `docs/issues/ISSUE-62-mvp-field-acceptance-e2e.md` rather than a second harness.

## Shipped on `main`

`make e2e` smoke path and field checklist doc on Balanced branches.

## Remaining scope

Owner field run; optional CI promotion after `#63` ruleset election and browser-cache budget.

## Wire fields

Fleet log keys per `RECORD_KEYS` / `docs/api-contract.md` (incl. `suddenFreq`, `nightNY`).

## Clamps / safety

C1 A2DP-only; Hold/Manual; no Web Bluetooth.

## Acceptance tests

Checklist items 1–11 in `docs/issues/ISSUE-62-mvp-field-acceptance-e2e.md`; local `make e2e` exits 0.

## CI gate

Informative e2e job today; required only after owner decision.

## Risks / HW limits

Soundcore DSP roll-off and night/local TZ skew are hardware/environment dependent.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/62
- `docs/issues/ISSUE-62-mvp-field-acceptance-e2e.md`
