# ISSUE-44 — Web PWA impulse→blast

**Status:** working slice (PR2) — Simulate impulse + volBlast jump toward VOL_PATCH_MAX with night/Hold clamps; multi-sample accel baseline warm-up (`ACCEL_BASELINE_WARM_N`) avoids gravity false blast; simulation enters extreme shriek/contour path via `noteImpulse` → `enterExtremeFromBurst`.

## Didn't

- Claim micDiff full AEC (#25 parked)
