# #145 — Background / continuous sensing constraints

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/145

## Status

**Implemented on this branch.** Policy + docs. No invented background entitlements.

## Goal

Honest OS limits for scientific ASP runs.

## Prior art

`docs/iphone-dedicated-mode.md`; Apple background modes. **Build** fail-closed pause.

## Shipped on `main`

None.

## Remaining scope

On-device lock test.

## Wire fields

None.

## Clamps / safety

No fake always-on mic. AC power ≠ background entitlement.

## Acceptance tests

`onEnterBackground` → backgroundPaused; rejected modes listed.

## CI gate

IoTASPSmoke + `tests/test_background_sensing.py`.

## Risks / HW limits

iOS will suspend. Guided Access is operational, not an API.

## Sources

Issue #145, `docs/ios-background-sensing.md`, Apple background execution docs.
