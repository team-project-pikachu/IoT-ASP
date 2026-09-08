# #6 — Material-dependent vibration channel selection (native)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/6 · Milestone: [iOS / iPhone](https://github.com/team-project-pikachu/IoT-ASP/milestone/10)

## Status

**Implemented on this branch (native).** `materialPreset` picker arms physical and/or acoustic. Backend `MATERIAL_CHANNEL_BIAS` already consumes the wire name.

## Goal

Choose physical vs acoustic (or both) from setup: table → physical; speaker radiate → both; handheld → acoustic; chair (#18) → physical.

## Prior art

`priors.MATERIAL_CHANNEL_BIAS`; spec 04-06 web `<select>` remaining. **Build** native arming; unknown preset falls back to `handheld` (bias 1.0 on backend for unknown strings).

## Shipped on `main`

Backend bias table. Phone did not emit `materialPreset`.

## Remaining scope

Web HTML select (spec 04-06). Telemetry POST of the preset → #147.

## Wire fields

`materialPreset`: handheld | table | chair | speaker. `vibClass`. No schemaVersion bump.

## Clamps / safety

Unknown preset → handheld locally. Hold / Manual unchanged.

## Acceptance tests

table/chair acoustic=false; speaker both; handheld acoustic-only; physical event ignored when physical disarmed; granite → handheld.

## CI gate

IoTASPSmoke + `tests/test_vib_channel_policy.py`.

## Risks / HW limits

Arming is policy, not a materials lab. Chair node still needs LF proxy (#18).

## Sources

Issue #6, `docs/specs/04-06-vibration-channels.md`, `priors.py` MATERIAL_CHANNEL_BIAS.
