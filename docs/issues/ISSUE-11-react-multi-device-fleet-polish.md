# ISSUE-11 — React multi-device fleet polish

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/11  
**Classification:** parked stub (Balanced election)  
**Owner surface:** frontend  
**Canonical spec / ADR:** `docs/specs/10-11-react-rewrite.md`

## Scope (this pass)

Parked React rewrite; Balanced pass shipped a **static** fleet card stub (BroadcastChannel) in public/index.html.

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

- Full React cards wait on #10
- Static stub is intentional
