# #150 — Wire native sensors into Nest / Glass Shatter tabs

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/150

## Status

**Implemented on this branch.** `ProductTabHooks` maps acoustic burst → `sound_burst` / HomeNestAlarm tab. Nest OAuth parked. Alarm demo without tokens. Hold wins.

## Goal

Phone mic/motion events feed the Nest/Glass product story without live Nest tokens.

## Prior art

M8 glass event PRs; `AlarmStateMachine`. **Build** mapping; do not invent OAuth.

## Shipped on `main`

Web Nest stubs. Native alarm only.

## Remaining scope

Live Nest when sibling milestone unparks OAuth.

## Wire fields

Event class names `sound_burst` | `glass_shatter` — local, not a schemaVersion bump.

## Clamps / safety

Hold refuses demo trigger. No Nest tokens.

## Acceptance tests

classify burst; hold wins; nestOAuthParked true.

## CI gate

IoTASPSmoke + `tests/test_product_tabs.py`.

## Risks / HW limits

Not a glass-shatter classifier.

## Sources

Issue #150, Nest milestone, `AlarmStateMachine`.
