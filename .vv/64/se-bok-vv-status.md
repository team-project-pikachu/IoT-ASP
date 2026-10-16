# SEBoK V&V status for #64

Evidence closeout for cross-cutting fleet invariants. No invented HW results, live URLs, or secrets.

## On main

- CI static gates (`scripts/ci_static_gates.sh`) enforce C1 (no Web Bluetooth TX patterns), C4 (`vol_hard_max=100`), HOLD1 (Hold/Manual freeze), SCH1 (`schemaVersion: 1` in contract and clamps).
- Unit tests in `tests/` cover clamp reject of vol>100, out-of-band freqs, hold refuse.
- Matrix remains living; rows stay `stub` or move to `in_progress` until field evidence from #62 lands.

## Residual

- Owner-signed field validation (Chrome iOS A2DP route, SPL honesty, LF HW) required for `pass`.
- Do not mark Project Done without fresh `.vv/` packages.

Invariants preserved: C1 native A2DP only; vol_hard_max=100; Hold/Manual freeze; no keys in public/; no schemaVersion bump.
