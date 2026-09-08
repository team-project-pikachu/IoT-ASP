# #151 — On-device verification / test plan

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/151

## Status

**Implemented on this branch (plan).** Humans execute. Studio is CLT-only.

## Goal

Repeatable on-device verification for native sensors + 17–23 kHz hop path.

## Prior art

`SYSTEMS-CHECK.md`, #112 CI stub. **Build** plan, not fake device results.

## Shipped on `main`

CLT smoke only.

## Remaining scope

Owner device run + fill matrix #149.

## Wire fields

None new.

## Clamps / safety

No invented entitlements. No PII in `.vv`.

## Acceptance tests

Plan file lists permission, 48 kHz, CoreMotion, routes, telemetry, background, SensorKit.

## CI gate

`tests/test_on_device_plan.py`.

## Risks / HW limits

CI cannot prove audio/motion.

## Sources

Issue #151, `docs/ios-on-device-verification.md`.
