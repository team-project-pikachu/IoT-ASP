# ISSUE-62 — MVP field acceptance + promote Playwright e2e

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/62  
**Canonical checklist:** [../field-acceptance-m0.md](../field-acceptance-m0.md) (C1–C6 mapped FA-01…FA-14)  
**Evidence:** [../../.vv/62/](../../.vv/62/) (`SOFTWARE-E2E.md`, `FIELD-PASS.md`)  
**Classification:** M0 docs + headless e2e deepen; **field lab owner-gated**; **e2e stays Informative**  
**Status (2026-09-08):** checklist in `docs/field-acceptance-m0.md`; Playwright MVP suite + `__hop` inject hooks; ruleset **not** changed (#63)

## Field checklist (3-phone fleet)

Safari + native **A2DP** only (C1) — not **Web Bluetooth**. Full tick list: [field-acceptance-m0.md](../field-acceptance-m0.md).

Summary:

1. A2DP 1:1 Soundcore (C1)
2. Signal on · incoherent hops (C3)
3. Hold / Manual (HOLD1)
4. suddenFreq rotate
5. Night-curve honesty (`nightNY` / NY window; C5-aware)
6. Soundcore roll-off warning (#43) + C6 LF gate honesty
7. fleet_log JSONL / optional #61 / no keys in HTML

## Local e2e

```bash
make e2e   # serves public/ + Playwright smoke (tests/e2e/)
# MVP-only: bash tests/e2e/run.sh --grep "MVP field acceptance"
```

### CI decision (AC #2) — Informative waiver

| Job | Ruleset | Notes |
|-----|---------|-------|
| `e2e smoke` | **Informative** (allowlisted non-required) | Stay so until owner **#63** election + `make protect-main` |

Do **not** edit `.github/rulesets/main-protection.json` for #62 alone. See [ci.md](../ci.md), [branch-protection.md](../branch-protection.md).

## Didn't

- Claim 3-phone field lab completed (needs devices + optional #61 URLs)
- Force e2e as a required check / edit `main-protection.json`
- Sonos (#39) or wire-backend (#61) implementation

## Next

- Owner run FA-01…FA-14; fill `.vv/62/FIELD-PASS.md`
- Optionally promote `e2e smoke` under #63
