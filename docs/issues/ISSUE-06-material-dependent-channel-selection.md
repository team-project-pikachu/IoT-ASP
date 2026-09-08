# ISSUE-06 — Material-dependent channel selection

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/6  
**Classification:** implemented (local worktree `IoT-ASP-wt-issue6` / `feat/6-material-channel-select`)  
**Owner surface:** frontend + backend policy  
**Canonical spec / ADR:** `docs/specs/04-06-vibration-channels.md`

## Scope (this pass)

Ship material → channel arming API + UI + wire emit; leave #4/#5 detector bodies to their owners.

## What landed locally

- Shared selector: `services/autoroute-adk/iot_asp_autoroute/vib_channel_select.py`
- Frontend mirror: `public/vib-channel-select.js` (`globalThis.IotAspVibChannelSelect`)
- `public/index.html`: `<select id="materialPreset">`, `armPhysical`/`armAcoustic` gates on `updateVibClass`, availability fallbacks, `materialPreset` in `telemetryPayload()`
- `priors.seismo_bundle()` exposes `materialChannelSelect`
- Tests: `tests/test_vib_channel_select.py`, `tests/test_priors_material.py`

## Selection rules

| Preset | Mode | Physical | Acoustic | Prefer |
|--------|------|----------|----------|--------|
| `table` | physical | ✓ | ✗ | physical |
| `chair` | physical | ✓ | ✗ | physical |
| `speaker` | both (→ acoustic if motion denied) | ✓ | ✓ | acoustic |
| `handheld` | both | ✓ | ✓ | acoustic |

## #4 / #5 hooks

- `#4`: before `forceHopFromShake` / physical `updateVibClass`, require `armPhysical`
- `#5`: before acoustic burst → `updateVibClass("acoustic")`, require `armAcoustic`
- Call `setPhysicalAvailable` / `setAcousticAvailable` (or refresh via armSensors) on permission results

## What did **not** land

- Merge with `feat/4-physical-vib` (shake hop / g-units) — expected conflict in `public/index.html` vib block
- Full #5 acousticBurst detector
- Commit / push (left uncommitted for election)

## Next

- Merge after #4 lands: keep #6 `materialPreset` / `refreshChannelArms` + #4 `forceHopFromShake` / g conversion
- Optional: arming checkboxes override beyond preset defaults
