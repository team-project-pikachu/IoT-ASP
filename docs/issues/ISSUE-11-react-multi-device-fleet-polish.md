# ISSUE-11 — React multi-device fleet polish

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/11  
**Classification:** M0 static fleet slice **done on `main`**; React-era polish **deferred** (depends on #10)  
**Owner surface:** frontend  
**Canonical spec / ADR:** `docs/specs/10-11-react-rewrite.md`

## M0 decision

Issue body: *"React-era multi-device fleet UX polish (device cards, seed compare, fleet health).
Depends on optional React rewrite. Labels: parked"*

Split for milestone closeout:

| Slice | M0 status | Evidence |
|-------|-----------|----------|
| Static fleet panel (seed compare, Simulate impulse, peer cards / BroadcastChannel) | **Shipped** on `main` via Balanced PR2 [#66](https://github.com/team-project-pikachu/IoT-ASP/pull/66) | `fleetSeedCompare`, `simImpulseBtn`, fleet panel in `public/index.html`; `tests/test_public_html.py` |
| Optional deepen (`#fleetBackendStrip`, stale peer CSS, gyro axes) | In open [#75](https://github.com/team-project-pikachu/IoT-ASP/pull/75) — not required to close #11 for M0 | PR7 Balanced |
| React / RSD device cards + cross-phone discovery | **Deferred** with #10 | Spec M0 deferral + unpark gates |

**Do not wait on React for M0.** Close #11 as M0-complete for the static slice; keep React polish as follow-up after #10 unparks (or leave a parked follow-up issue).

## Scope (this pass)

Document M0 closeout only. No React rewrite. No further `public/index.html` churn in this PR.

## Did (already on `main`)

- `public/index.html` fleet cards + BroadcastChannel heartbeat + seed compare strip
- Tests: `simImpulseBtn`, `fleetSeedCompare`, `copyFleetLogBtn`

## Didn't

- React / RSD rewrite (#10 still parked / deferred past M0)
- Cross-phone discovery (needs native / #10)
- Claiming live multi-device field acceptance (that is `#62`)

## Next

- Milestone closeout: remove #11 from M0 (or close as static slice done + React deferred).
- React-era cards wait on #10 unpark criteria in `docs/specs/10-11-react-rewrite.md`.
- Field UX acceptance remains `#62` / `#61` (live URLs), not this issue.
