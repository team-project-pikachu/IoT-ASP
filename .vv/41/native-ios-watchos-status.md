# #41 Native iOS + watchOS status (2026-11-27)

## Summary
Unsigned buildable scaffold exists under `native/IoTASP/`. Full Xcode signing, on-device validation, SensorKit entitlement, and Watch connectivity remain owner-gated (no full Xcode on CI; no invented HW results).

## Acceptance mapping
- Scaffold present: yes (prior PR #40 referenced in issue).
- `swift test` / plutil gates: as documented in spec.
- Device signing / SensorKit / live A2DP validation: residual, owner hardware required.

## Invariants preserved
- C1 native iOS A2DP only.
- vol_hard_max=100.
- Hold/Manual freeze.
- No schemaVersion bump.
- No keys in public/.
- No secrets or live URLs invented.

## Out of scope
- Full Xcode.app builds.
- SensorKit entitlement paperwork.
- Live device test results.

Evidence only; no product code change.
