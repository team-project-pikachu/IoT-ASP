# ISSUE-24 — google-adk / google-genai 2.x

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/24  
**Classification:** parked stub (Balanced election)  
**Owner surface:** backend  
**Canonical spec / ADR:** `docs/specs/24-adk-2x-migration.md`

## Scope (this pass)

Keep major-1 ADK pin on main. Optional example pins in requirements-adk2.example.txt only.

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

- Do not bump requirements.txt until unparked
- Import smoke when unparked
