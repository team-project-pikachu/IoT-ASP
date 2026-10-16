# SEBoK V&V matrix pass status — #64

Evidence package for issue #64: move cross-cutting Req IDs C1-BT, C3-SDD, C4-VOL, C5-120V, C6-LF, SCH1, HOLD1 from stub → pass based on existing on-main packages under `.vv/12/`, `.vv/16/`, `.vv/17/` and clamps/docs.

**Revision cited:** main @ dab7afb1 (2026-10-16 queue run)

## Mapping

| Req ID | Status | Evidence |
|--------|--------|----------|
| C1-BT | pass | `.vv/12/` code/docs audit: no Web Bluetooth TX; Chrome iOS uses system BT. See DESIGN_CONSTRAINTS. |
| C3-SDD | pass | `.vv/12/` UI + autoroute loop; Hold/Manual override documented. |
| C4-VOL | pass | `clamps.py` vol_hard_max=100; `.vv/12/observed-results.md` V-12-A/B; dry-run OK. |
| C5-120V | pass | Schema + dry-run fixtures use power=ac120; `.vv/12/`, `.vv/17/`. |
| C6-LF | pass | Gate respected; band tags; `.vv/12/`, `.vv/16/`. HW honesty when na. |
| SCH1 | pass | schemaVersion:1 asserted in dry-run; frontend polls only, no keys. |
| HOLD1 | pass | `.vv/12/observed-results.md` V-12-D; worker + frontend early-return on holdManual. |

## Negative controls

- Bad patch / vol>100 rejected: `.vv/12/negative-controls.md` + dry_run.py asserts.
- Hold blocks apply: confirmed in observed-results.

## Residual (out of scope for this closeout)

- Live production Vercel 200 / full HW field runs deferred to integrate / #62.
- Full #9 SensorKit, parked #14/#15.
- No invented live URLs, secrets, or hardware results.

## Invariants preserved

- No schemaVersion bump.
- vol_hard_max=100.
- Hold/Manual freeze.
- No keys in public/.

Matrix rows updated in `.vv/matrix.md`. Spec status: Done on main for these Req IDs via existing evidence.
