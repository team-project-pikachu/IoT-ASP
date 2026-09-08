# #99 — Glass shatter privacy / recording consent

## Status

Public-safe consent + retention checklist shipped; live Nest recording / OAuth consent remains owner-gated (#93 parked).

## Goal

Define **recording consent, retention, and redaction rules** for glass-shatter audio/video *context*
so agents and CI never put credentials, clip URLs, or site PII in the public repo — while owners
know what must be acknowledged before live Nest / Gemini paths.

## Prior art

- [`docs/nest-device-access.md`](../nest-device-access.md) §7 Privacy posture (clip URLs, device refs).
- [`docs/STUDY_PRIVATE.md`](../STUDY_PRIVATE.md) — private study companion pointer.
- Nest detector prompt contract: features only — no audio bytes / URLs / raw ids
  (`iot_asp_autoroute/nest/detector.py` `_prompt_payload`).
- Fleet invariant: no site PII in telemetry ([`docs/api-contract.md`](../api-contract.md)).

## Shipped on `main`

| Artifact | Role |
|----------|------|
| `docs/nest-device-access.md` §6–§7 | Secret **names** + privacy posture |
| `nest/mapping.py` `device_ref` | Truncated hash instead of raw SDM id |
| `nest/detector.py` | Advisory classify; never writes patches; no media in prompt |
| `docs/STUDY_PRIVATE.md` | Points at gitignored / private companion |

## Remaining scope

- Owner-facing in-app consent copy on HomeNest / PWA when live linking ships (#97 / #101).
- Live OAuth consent screen steps stay on #93 (parked — agents do not browser-login).
- Retention TTLs for private `meta/nest/` objects — owner GCS policy (not public git).

## Consent checklist (owner)

Before enabling live Nest CameraSound → glass_shatter escalation:

1. [ ] Consumer Google Account owns Nest devices (Device Access requirement).
2. [ ] Device Access + GCP OAuth completed per [`docs/nest-device-access.md`](../nest-device-access.md).
3. [ ] Secrets only in 1Password Environment `dev` / Secret Manager (**names** in git).
4. [ ] Understand: CameraSound is a **detection signal**, not an audio file; ClipPreview URLs
      are recording URIs — private only.
5. [ ] Agree: public telemetry may carry `nestBurstClass` / `nestDeviceRef` / `soundBurst` /
      `alarmState` / `volBlast` — never preview URLs, street addresses, or neighbor identifiers.
6. [ ] Agree: Hold / Manual must clear louder escalation; false glass_shatter must not fire
      without corroboration policy in `offline_classify`.
7. [ ] Gemini Enterprise / metered calls only after explicit owner confirmation.

Public copy of this list: [`docs/glass-shatter-privacy.md`](../glass-shatter-privacy.md).

## Wire fields

Canonical [`docs/api-contract.md`](../api-contract.md). Privacy-relevant Nest additives:

| Field | Public wire? | Notes |
|-------|--------------|-------|
| `nestBurstClass` | yes | `glass_shatter` \| `sound_burst` \| `other` |
| `nestBurstConfidence` | yes | scalar |
| `nestBurstSource` | yes | `offline_heuristic` \| `gemini_enterprise` |
| `nestDeviceRef` | yes | truncated hash only |
| `nestClipAvailable` | yes | boolean — no URL |
| Clip `previewUrl` / raw device id | **never** | private `meta/nest/` or memory |

## Clamps / safety

- No credentials in repo, chat, issues, or `.vv` evidence.
- Detector is advisory; `escalation_hint(..., hold_manual=True)` returns `{}`.
- Agents never scrape Nest / Home consoles or mint OAuth interactively.

## Acceptance tests

| ID | Check |
|----|--------|
| GP-01 | Spec + `docs/glass-shatter-privacy.md` list consent items 1–7 |
| GP-02 | Docs name secret **env var names** only (no token shapes / pasted secrets) |
| GP-03 | Docs forbid clip URLs and raw SDM ids on the public wire |
| GP-04 | Cross-link #93 as parked (no live OAuth required to close #99 docs) |

Evidence: [`.vv/99/CHECKLIST.md`](../../.vv/99/CHECKLIST.md).

## CI gate

Docs only for this issue. Sentinel / redaction coverage remains in Nest offline tests
(`tests/test_nest_sdm.py`, `tests/test_nest_events.py`) and #98 E2E detector tests when merged.

## Risks / HW limits

- Live stream Opus (tier-2 audio) is parked — would expand consent surface if ever enabled.
- Private study recordings are out of band (`IoT-ASP-study`); never subtree into public `main`.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/99
- https://developers.google.com/nest/device-access/traits/device/camera-sound
- https://developers.google.com/nest/device-access/traits/device/camera-clip-preview
- [`docs/nest-device-access.md`](../nest-device-access.md)
- [`docs/STUDY_PRIVATE.md`](../STUDY_PRIVATE.md)
- [`docs/api-contract.md`](../api-contract.md)
