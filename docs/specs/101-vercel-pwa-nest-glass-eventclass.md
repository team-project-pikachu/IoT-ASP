# Spec — Vercel PWA Nest/SDM + glass_shatter eventClass (#101)

**Surface:** `public/` PWA (Vercel).  
**Status:** UI/telemetry stub — live Nest OAuth / Pub/Sub remain owner-gated.

## Acceptance

- Fleet + monitor show additive `eventClass`: `sound_burst` | `glass_shatter` | `CameraSound` (SDM CameraSound) | `none`
- Simulate buttons escalate louder alarm via existing `alarmState` / `volBlast` (no Nest credentials in repo or browser)
- Wire field stays optional on `schemaVersion: 1` (see `docs/api-contract.md`)

## Out of scope

- Device Access console / OAuth tokens (owner: bettyctai@gmail.com)
- Live SDM Pub/Sub subscription (#103 research)
