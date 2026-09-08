# ISSUE-02 — Max-entropy seeds

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/2  
**Classification:** parked stub (Balanced election)  
**Owner surface:** frontend  
**Canonical spec / ADR:** `docs/specs/02-max-entropy-seeds.md`

## Scope (this pass)

Already largely on main (entropySeed/Reseed/watchdog). This note parks further polish.

## Constraints

- No site PII in public docs.
- Do not invent secrets, entitlements, or HW capabilities.
- Prefer linking existing `docs/specs/` over forking tables (`docs/api-contract.md` is wire canon).

## What landed locally

- This stub note under `docs/issues/`.
- Pointers to existing specs / code hooks only.

## What did **not** land

- Full product implementation for this issue.
- Live HW / Notion / HomeKit / Pi / ADK 2.x bumps where listed as parked.

## Next

- No further seed UI until unparked
- Keep mulberry32 + localStorage hop.seed
