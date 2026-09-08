# ISSUE-03 — Continuous polling & monitoring

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/3  
**Classification:** implemented (M2 / GitHub milestone 3)  
**Owner surface:** frontend  
**Canonical spec / ADR:** `docs/specs/03-continuous-monitoring-watchdog.md`

## Scope (this pass)

Close residual #3 surface after per-device watchdog landed on `main` via #29/#33:

- Fleet heartbeat view for “all 3 phones on” (`#fleetHealth`, STALE cards, watchdog fields on BroadcastChannel snaps)
- Monitor panel polish: live `#telSnr` / additive `micSnr` alongside `|a|` / micEnergy
- Unpark Balanced board classification

## Constraints

- No site PII in public docs.
- Do not invent secrets, entitlements, or HW capabilities.
- Prefer linking existing `docs/specs/` over forking tables (`docs/api-contract.md` is wire canon).
- Nest continuous poller (#108) stays a Related M8 lane — not this PR.

## What landed

- Per-device 1 s watchdog + AudioContext auto-resume + Monitor hop/resume/trip cells (already on `main`).
- Fleet pulse strip + enriched peer heartbeats (`running`, `lastHopAgeMs`, `ctxResumes`, `watchdogTrips`, `micSnr`).
- Monitor `SNR` cell fed from decoder / sudden-onset band SNR (`lastMicSnr`).
- Docs / Balanced status unparked for #3.

## Parked follow-ups (out of M2 close)

- Cross-device heartbeats without same-origin tabs (native / #10 React rewrite).
- iOS background `Worker` tick; osc/gain health beyond null-check.
- Do not block Vercel ship.
