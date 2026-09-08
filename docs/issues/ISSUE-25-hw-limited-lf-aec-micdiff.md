# ISSUE-25 — HW-limited LF/AEC micDiff

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/25  
**Classification:** parked stub (Balanced election)  
**Owner surface:** backend+frontend  
**Canonical spec / ADR:** `docs/specs/25-hw-limited-lf-aec-micdiff.md`

## Scope (this pass)

Best-effort micDiff shipped; full AEC / LF mic / LF TX remain HW-limited.

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

- Do not claim full AEC
- lfDriveCapable default false
