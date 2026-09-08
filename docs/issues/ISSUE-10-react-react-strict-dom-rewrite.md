# ISSUE-10 — React / React Strict DOM rewrite

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/10  
**Classification:** parked — **deferred past M0** (tracking only; not a ship blocker)  
**Owner surface:** frontend  
**Canonical spec / ADR:** `docs/specs/10-11-react-rewrite.md`

## M0 decision

Issue body: *"Optional rewrite of static `public/index.html` to React / React Strict DOM. Do not
block shipping the static blaster. Milestone: M0 (tracking only) or later polish."*

**Do not implement the rewrite for M0.** Close or remove from milestone/1 after the deferral
section in `docs/specs/10-11-react-rewrite.md` is on `main`. Reopen / unpark only when the
**Unpark #10** criteria in that spec are met.

## Scope (this pass)

Parked. Static `public/index.html` remains the ship path. Thin docs only: Prior art, refreshed
bundle size, explicit M0 deferral + unpark gates.

## Constraints

- No site PII in public docs.
- Do not invent secrets, entitlements, or HW capabilities.
- Prefer linking existing `docs/specs/` over forking tables (`docs/api-contract.md` is wire canon).
- No `web/` scaffold, no React / RSD dependencies, no deploy pipeline change.

## What landed locally

- Spec deferral + Prior art + size refresh in `docs/specs/10-11-react-rewrite.md`.
- This stub note under `docs/issues/`.

## What did **not** land

- React / React Strict DOM rewrite.
- Any change to `public/index.html` for this issue.

## Next

- Milestone closeout: remove #10 from M0 (or close as deferred).
- Unpark only per spec criteria after `#62` field acceptance.
