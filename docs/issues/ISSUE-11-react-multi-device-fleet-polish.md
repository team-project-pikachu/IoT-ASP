# ISSUE-11 — React multi-device fleet polish

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/11  
**Classification:** parked React rewrite; **static fleet slice deepened** (Balanced PR2)  
**Owner surface:** frontend  
**Canonical spec / ADR:** `docs/specs/10-11-react-rewrite.md`

## Scope (this pass)

Parked full React rewrite (#10). Static PWA fleet panel now has seed compare, peer staleness, impulse/blast badges, Simulate impulse.

## Did

- `public/index.html` fleet cards + BroadcastChannel heartbeat + seed compare strip
- Tests: `simImpulseBtn`, `fleetSeedCompare`, `copyFleetLogBtn`

## Didn't

- React / RSD rewrite (#10 still parked)
- Cross-phone discovery (needs native / #10)

## Next

- Full React cards wait on #10
