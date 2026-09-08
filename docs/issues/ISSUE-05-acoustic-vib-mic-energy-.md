# ISSUE-05 — Acoustic vib (mic energy)

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/5  
**Classification:** implemented (local worktree `feat/5-acoustic-vib`)  
**Owner surface:** frontend (`public/acoustic-vib-energy.js` + `public/index.html` `#5` block)  
**Canonical spec / ADR:** `docs/specs/04-06-vibration-channels.md`

## Scope (this pass)

Promote the absolute `acousticEnergy > -55 dB` vib class rule to a **1 s rolling-median burst** detector (≥12 dB) on hop-band energy, preferring `micDiff` when available so self-TX does not rotate hops. Burst rising edge forces a hop (debounce ≥300 ms) when *Vib auto* is on and `armAcoustic` is true.

## Constraints

- No site PII in public docs.
- Do not invent secrets, entitlements, or HW capabilities.
- Prefer linking existing `docs/specs/` over forking tables (`docs/api-contract.md` is wire canon).
- Do not own DeviceMotion (#4) or materialPreset arming UI (#6); only consume `armAcoustic` (default `true`).

## What landed locally

- `public/acoustic-vib-energy.js` — tracker + `preferEnergy` (global `IotAspAcousticVib`).
- `services/autoroute-adk/iot_asp_autoroute/acoustic_vib_energy.py` — Python twin.
- `public/index.html` — `// ══ vib channels (#5)` wire-up, mic teardown reset, `__hop.getState` acoustic fields.
- `tests/test_acoustic_vib_energy.py` + static HTML asserts.

## What did **not** land

- Material / arming UI (`materialPreset` select) — owned by #6.
- DeviceMotion gravity/g/`shake` path — owned by #4.
- Closing the GitHub issue (needs live mic verification on device).

## Verify

1. Serve `public/` over https/localhost; open the blaster.
2. Tap **Vib auto**, then **Listen** (allow mic; AEC/NS/AGC off).
3. Produce a short US/hop-band energy burst (or clap near a US-capable mic path); pill → `acoustic`, algo → `pulse`/`hop`, monitor log `acoustic burst → hop`.
4. Tap **Stop** on Listen — tracker resets; acoustic class clears.
5. `python3 -m pytest tests/test_acoustic_vib_energy.py tests/test_public_html.py -q`

## Next

- Reconcile merge with #4/#6 on `public/index.html` (`armAcoustic` declared in all three).
- Coupled polish with #25 HW limits / calibrated SPL.
