# #148 — Apple Developer / SensorKit entitlement approval checklist

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/148

## Status

**Implemented on this branch (docs).** Checklist is unchecked. No fake approval artifacts.

## Goal

Actionable human checklist complementary to #113.

## Prior art

#113 privacy docs; entitlements example files on PR #132. **Build** checklist only.

## Shipped on `main`

Entitlement commented out in `IoTASP.entitlements`.

## Remaining scope

Owner portal steps. Do not automate.

## Wire fields

None.

## Clamps / safety

No invented grants. CI stub until evidence.

## Acceptance tests

Checklist file exists; boxes unchecked; no `approved: true` fake JSON.

## CI gate

`tests/test_sensorkit_checklist.py`.

## Risks / HW limits

Without grant, entitled path stays dark.

## Sources

Issue #148, Apple SensorKit program docs, #113.
