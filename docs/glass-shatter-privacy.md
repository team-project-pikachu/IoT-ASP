# Glass shatter — privacy & recording consent

**Issue:** [#99](https://github.com/team-project-pikachu/IoT-ASP/issues/99)  
**Spec:** [`docs/specs/99-glass-shatter-privacy.md`](specs/99-glass-shatter-privacy.md)  
**Related:** [`docs/nest-device-access.md`](nest-device-access.md) · [`docs/STUDY_PRIVATE.md`](STUDY_PRIVATE.md)

Public-safe owner checklist. No credentials, Device Access UUIDs, or clip URLs belong in this file.

## What the public fleet may observe

- Nest **CameraSound** (and related) as an event *class* + timestamp.
- Phone ASP features (`micDiff`, `bandBurst`, `soundBurst`, …) per the API contract.
- Advisory labels `glass_shatter` / `sound_burst` / `other` and alarm hints (`alarmState`, `volBlast`)
  when not under Hold / Manual.

## What must stay private

- OAuth client secrets, refresh tokens, access tokens.
- CameraClipPreview `previewUrl`, still-image URLs, raw SDM device / structure ids.
- Street addresses, neighbor identifiers, recording URIs (study package / private GCS only).

## Owner consent (tick before live linking)

1. [ ] I own the Nest devices on a consumer Google Account eligible for Device Access.
2. [ ] I completed Device Access + GCP OAuth using secret **names** from 1Password `dev` only.
3. [ ] I understand CameraSound is a detection signal (no audio file from SDM on that event).
4. [ ] I will not commit clip URLs, tokens, or site PII to the public repo or `.vv/` evidence.
5. [ ] I accept Hold / Manual as the hard stop for louder escalation.
6. [ ] I will not enable metered Gemini / paid API `--apply` without an explicit decision.
7. [ ] Live OAuth consent UI steps remain under [#93](https://github.com/team-project-pikachu/IoT-ASP/issues/93) (parked for agents).

## Retention (policy pointer)

Retention TTLs for private Nest artifacts live in owner GCS / Secret Manager policy — not in public
git. Private study protocol: companion `IoT-ASP-study` via [`STUDY_PRIVATE.md`](STUDY_PRIVATE.md).
