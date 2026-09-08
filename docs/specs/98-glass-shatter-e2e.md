# #98 — Glass shatter E2E acceptance

## Status

Offline E2E acceptance + pytest scaffold shipped; physical Nest shatter trial and live notify remain owner-gated.

## Goal

Prove the **simulate → classify → escalate louder → snapshot context stub → notify pending** path for
`glass_shatter` without requiring live OAuth or proprietary GoogleHomeSDK in CI.

## Prior art

- Issue #98 goal: simulate glass shatter → classify → escalate louder → snapshot context stub → notify pending flag.
- Nest detector on `main`: `iot_asp_autoroute/nest/detector.py` (`offline_classify`, `escalation_hint`).
- Field checklist pattern: [`docs/issues/ISSUE-62-mvp-field-acceptance-e2e.md`](../issues/ISSUE-62-mvp-field-acceptance-e2e.md).
- PWA alarm machine: `alarmState` / `volBlast` / Hold ([`docs/api-contract.md`](../api-contract.md)).
- Platform matrix: [#100](https://github.com/team-project-pikachu/IoT-ASP/issues/100) · Privacy: [#99](https://github.com/team-project-pikachu/IoT-ASP/issues/99).
- Docs drain index: [`docs/milestones/M8-docs-acceptance.md`](../milestones/M8-docs-acceptance.md).
- Feature stack (UI / native — **not** duplicated here): [#114](https://github.com/team-project-pikachu/IoT-ASP/pull/114) (#96), [#115](https://github.com/team-project-pikachu/IoT-ASP/pull/115) (#101 PWA), [#116](https://github.com/team-project-pikachu/IoT-ASP/pull/116) (#102 Playground), [#117](https://github.com/team-project-pikachu/IoT-ASP/pull/117) (#97 Home wiring).

## Shipped on `main`

| Step | Artifact |
|------|----------|
| Classify | `nest/detector.offline_classify` → `glass_shatter` \| `sound_burst` \| `other` |
| Escalate hint | `nest/detector.escalation_hint` → `alarmState` / `volBlast` / `trigger` |
| Hold wins | `escalation_hint(..., hold_manual=True) == {}` |
| Nest event parse | `nest/events.py` + fixtures under `tests/fixtures/nest/` |
| Wire map | `nest/mapping.event_to_telemetry` (no clip URL leak) |

## Remaining scope

| Item | Gate |
|------|------|
| Physical glass / recorded shatter trial | Owner lab + private evidence |
| HomeNest UI “Simulate glass shatter” | #97 / PR [#117](https://github.com/team-project-pikachu/IoT-ASP/pull/117) (stacks on #114) |
| Push / Automation notify | Honest **pending** (#97 / PR #117) |
| PWA eventClass surface | #101 / PR [#115](https://github.com/team-project-pikachu/IoT-ASP/pull/115) |
| AcousticEventClass + gemini-burst-detect | #96 / PR [#114](https://github.com/team-project-pikachu/IoT-ASP/pull/114) |
| Swift Playground / home-ios-build | #102 / PR [#116](https://github.com/team-project-pikachu/IoT-ASP/pull/116) |
| Live Gemini Enterprise classify | Owner ADC + engine |

## Wire fields

Canonical [`docs/api-contract.md`](../api-contract.md). E2E asserts:

- Classification label whitelist: `glass_shatter` \| `sound_burst` \| `other`
- Escalation hints only use existing `alarmState`, `volBlast`, `trigger`
- Additive Nest telemetry: `nestBurstClass`, `nestBurstConfidence`, `nestBurstSource`, …
- No `previewUrl`, bearer tokens, or raw device ids on the wire

## Clamps / safety

- Hold / Manual blocks escalation hints.
- Offline path is default in CI (no network).
- Snapshot context is a **stub flag** (`nestClipAvailable` or local stub) — never a public URL.

## Acceptance tests

Human checklist: [`docs/issues/ISSUE-98-glass-shatter-e2e.md`](../issues/ISSUE-98-glass-shatter-e2e.md).

Offline IDs (enforced by `tests/test_glass_shatter_e2e.py`):

| ID | Statement |
|----|-----------|
| GS-01 | Strong Nest acoustic + phone corroboration → `glass_shatter` |
| GS-02 | Nest acoustic + weak corroboration → `sound_burst` (not glass) |
| GS-03 | `glass_shatter` → escalation hint with `volBlast: true` |
| GS-04 | `holdManual` → empty escalation hint |
| GS-05 | `as_wire()` never contains URL / token / raw id sentinels |
| GS-06 | Notify remains **pending** (documented; no false “shipped” claim) |
| GS-07 | Spec + ISSUE checklist files present |

```bash
python3 -m pytest tests/test_glass_shatter_e2e.py -q
```

Evidence: [`.vv/98/`](../../.vv/98/).

## CI gate

`tests/test_glass_shatter_e2e.py` is stdlib/pytest, offline. Promote as required check only after
owner `#63` election (same honesty as #62 e2e).

## Risks / HW limits

- SDM CameraSound carries no audio — glass label is fused evidence, not a spectrogram proof.
- Physical shatter trials may need private study retention rules (#99).
- CLT-only hosts may lack XCTest for native UI simulate buttons.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/98
- https://developers.google.com/nest/device-access/traits/device/camera-sound
- `services/autoroute-adk/iot_asp_autoroute/nest/detector.py`
- [`docs/api-contract.md`](../api-contract.md)
