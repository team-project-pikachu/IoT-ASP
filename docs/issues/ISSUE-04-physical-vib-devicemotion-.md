# ISSUE-04 — Physical vib (DeviceMotion)

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/4  
**Classification:** implemented (frontend #4 slice) — #5/#6 arming UI still parked  
**Owner surface:** frontend  
**Canonical spec / ADR:** `docs/specs/04-06-vibration-channels.md`

## Scope (this pass)

DeviceMotion linear accel in **g**, gravity-EMA fallback when `acceleration` is null, and **shake → force hop / reseed** (every 4th shake).

## Constraints

- No site PII in public docs.
- Do not invent secrets, entitlements, or HW capabilities.
- Prefer linking existing `docs/specs/` over forking tables (`docs/api-contract.md` is wire canon).

## What landed locally

- `public/index.html`: `MS2_TO_G`, gravity EMA (τ≈2 s), `forceHopFromShake`, `armPhysical`/`armAcoustic` defaults.
- Static gate `tests/test_public_html.py::test_physical_vib_devicemotion`.
- Backend negative-control `tests/test_priors_material.py` (material bias + Hold refuse).

## What did **not** land

- #5 acoustic burst detector polish.
- #6 `materialPreset` `<select>` / channel-arming UI (defaults both armed).
- Live phone HW verification on Safari (needs gesture + HTTPS).

## Next

- #6 material preset UI + emit `materialPreset` on wire.
- See #18 for chair bias / `infra_felt` deepen.
