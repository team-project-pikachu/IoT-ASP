# Evidence — #62 MVP field acceptance + Playwright e2e

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/62  
**Date scaffolded:** 2026-09-08  
**Environment:** docs + headless Chromium (CI / `make e2e`); Safari A2DP field lab **not** executed in this shard  
**Secrets:** none  
**Site PII:** none

## Procedure (verify lane)

1. Read `docs/field-acceptance-m0.md` (FA-01…FA-14) and `docs/DESIGN_CONSTRAINTS.md` C1–C6.
2. Run `make e2e` (or CI job `e2e smoke`) against `public/`.
3. Confirm `docs/ci.md` still lists `e2e smoke` as **informative** (non-required allowlist).

## Procedure (validate lane — owner)

1. Three phones + three Soundcore 2 on AC; pair 1:1 via Settings → Bluetooth.
2. Tick FA-01…FA-14 on a live hop-ultrasonic (or local `public/`) session.
3. Fill [FIELD-PASS.md](FIELD-PASS.md) with date, devices, pass/fail, notes.
4. Close #62 only after a completed dated field pass + green informative e2e on the merge SHA.

## Observed (this shard)

| ID | Result |
|----|--------|
| Checklist in `docs/` | pass (canonical `field-acceptance-m0.md`) |
| Playwright deepen (Soundcore banner, sudden controls, nightNY, Systems Soundcore row) | pass when `make e2e` green |
| Required-check promotion | **waived** → remain informative; owned by #63 |
| 3-phone field lab | **pending** (owner) |

## Files

- `docs/field-acceptance-m0.md`
- `docs/issues/ISSUE-62-mvp-field-acceptance-e2e.md`
- `docs/specs/62-mvp-field-acceptance-e2e.md`
- `docs/ci.md`
- `tests/e2e/public_smoke.spec.mjs`
- `.vv/62/FIELD-PASS.md`
