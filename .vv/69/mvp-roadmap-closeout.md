# #69 — Durable product roadmap closeout

**Date:** 2026-09-11  
**Worker:** iot-asp-issue-queue-drain  
**Branch:** `queue/#69-mvp-roadmap-closeout`

## Acceptance mapping

| Acceptance item | Status on main |
|-----------------|----------------|
| `docs/mvp-roadmap.md` lists milestones with issue #s | **Superseded pointer** — file exists; redirects to canonical `docs/roadmap.md` |
| Parked vs active called out | Yes — `parked` label + roadmap drain-order + milestone tables |
| Constraints C1/C2 noted | Yes — `docs/roadmap.md` Invariants + DESIGN_CONSTRAINTS |
| Links to live app, specs index | Yes — live app, Project 5, specs/README, closed-log |
| No parallel board taxonomy | Canonical is OS/product milestones (iOS, macOS, Nest, Sonos, Platform) |

## Files verified (main @ dab7afb1)

- `docs/roadmap.md` — canonical product plan (OS/surface milestones)
- `docs/mvp-roadmap.md` — legacy pointer kept for old links (#69, closed-log)
- `docs/specs/69-mvp-roadmap.md` — issue spec (updated by this PR to Done)
- `docs/mvp-closed-log.md` + `scripts/mvp_closed_log_append.sh` — closed chronology (#68)

## Out of scope / not claimed

- Live secret VALUES (#27), full HW LF/AEC (#25), live GCS creds (#26)
- Branch-protection ruleset apply on GitHub UI (#63) — docs only here
- Fabricated Nest/SensorKit approvals

## Invariants preserved

- C1 native iOS A2DP only
- `vol_hard_max=100`
- Hold/Manual freeze
- No schemaVersion bump (docs only)
- No keys in `public/`

## Residual

Milestone row ownership updates continue via normal PR hygiene; closes go to `mvp-closed-log.md`.
