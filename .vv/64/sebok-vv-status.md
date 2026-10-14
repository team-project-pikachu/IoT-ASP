# SEBoK V&V status for #64 — 2026-10-14

Docs/evidence slice only. Does not mark any matrix row `pass`. Field/HW validate remains owner-gated after #62 field acceptance.

## Acceptance mapping

| Req | Current on main | Evidence path | Status |
|-----|-----------------|---------------|--------|
| C1-BT | Code audit: no Web Bluetooth TX path in public/ or services/ | docs/DESIGN_CONSTRAINTS.md, public/index.html | in_progress (code) |
| C3-SDD | Autoroute loop + Hold/Manual documented | services/autoroute-adk/, docs/ | in_progress |
| C4-VOL | clamps.py vol_hard_max=100; unit tests reject >100 | services/autoroute-adk/iot_asp_autoroute/clamps.py, tests/ | in_progress (CI) |
| C5-120V | Schema allows power=ac120; dry-run fixtures | .vv/12/, schema | in_progress |
| C6-LF | Gate + band tag in clamps; LF skip when not capable | clamps.py, tests/ | in_progress (CI) |
| SCH1 | schemaVersion: 1 asserted in dry-run / contract | docs/api-contract.md | in_progress |
| HOLD1 | Hold flag freezes patch apply | tools.py / worker path, tests/ | in_progress (CI) |
| I12-* | Closed #12 evidence folders exist | .vv/12/ | stub (refresh residual) |

## What this PR ships
- This status note under `.vv/64/`.
- Matrix status column updated from `stub` → `in_progress` for C1/C4/C5/C6/SCH1/HOLD1 (CI/code evidence only).
- Spec stub `docs/specs/64-sebok-vv.md`.

## Out of scope (do not invent)
- Field validate on 3-phone A2DP fleet (#62).
- Live HW LF/AEC results (#25).
- Marking any row `pass` without dated field package.
- Secrets, live URLs, schemaVersion bump.

## Invariants preserved
- vol_hard_max=100
- Hold/Manual freeze
- No keys in public/
- C1 native iOS A2DP only

## Next
Owner attach field evidence after #62 → promote rows to `pass` and close #64.
