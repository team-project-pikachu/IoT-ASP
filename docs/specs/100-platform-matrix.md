# #100 — Platform matrix: Vercel / iOS / Playground × Nest hardware × SDM events

## Status

Docs acceptance matrix shipped; live Nest SDM → PWA / GoogleHomeSDK cells remain owner-gated.

## Goal

Publish one living matrix of **delivery surfaces × Nest hardware × SDM / ASP event classes** so M8 work
(#83–#104) can be tracked without conflating stub, dry-run, and live gates.

## Prior art

- Issue body tables (surfaces / hardware / events) — source of truth for this wave.
- [`docs/nest-device-access.md`](../nest-device-access.md) — owner Device Access / OAuth / Pub/Sub steps.
- Nest backend on `main`: `services/autoroute-adk/iot_asp_autoroute/nest/` (events, mapping, detector).
- Sibling surfaces (other PRs / stacked M8): Vercel PWA UI (#101), Swift Playground (#102),
  `native/IoTASPHome` (#91 / PR #105 stack).
- Alarm wire already on the PWA: `alarmState`, `volBlast`, `holdManual` in [`docs/api-contract.md`](../api-contract.md).

## Shipped on `main`

| Artifact | Role |
|----------|------|
| `docs/nest-device-access.md` | Console / secret-name owner steps |
| `iot_asp_autoroute/nest/events.py` | SDM event parse (CameraSound, ClipPreview, …) |
| `iot_asp_autoroute/nest/mapping.py` | Nest → additive `schemaVersion: 1` telemetry |
| `iot_asp_autoroute/nest/detector.py` | Offline + Gemini advisory `glass_shatter` / `sound_burst` |
| `public/index.html` | ASP blaster + `alarmState` / `volBlast` (no Nest UI yet) |
| `native/IoTASP/` | ASP ultrasonic shell (not HomeNest) |

## Remaining scope

| Cell | Owner |
|------|-------|
| Nest SDM webhook → PWA event UI | #101 |
| Swift Playground package workflow | #102 |
| Live GoogleHomeSDK + OAuth device run | #83 / #93 (parked) |
| Pub/Sub continuous → louder alarm in prod | #103 |
| Physical Nest cam / doorbell ladder | #104 |

## Delivery surfaces

| Surface | Support target | Stub now | Live gate |
|---------|----------------|----------|-----------|
| Vercel webapp / PWA | ASP blaster + event UI | telemetry + louder alarm path | Nest SDM → PWA (#101) |
| iOS Xcode / Swift | `native/IoTASPHome` HomeNestAlarm + Glass Shatter | `make home-ios-build` when package lands | GoogleHomeSDK + OAuth |
| Swift Playground | learning / prototype package | SPM stub (#102) | Playgrounds app session |

## Hardware rows

| Hardware | Sound path | Notes |
|----------|------------|-------|
| Nest cam (wired) | CameraSound / mic | SDM traits |
| Nest cam (battery) | CameraSound | power / event limits |
| Nest cam floodlight | CameraSound + Motion | correlate ClipPreview |
| Nest doorbell | CameraSound / Person | |
| Phone mic | ASP `micDiff` | existing PWA / native |
| Sonos / ASP speakers | louder alarm sink | `volBlast` escalation |

## Event classes

| Class | Source | Acceptance |
|-------|--------|------------|
| `sound_burst` | ASP / Nest detector | escalate louder when corroborated |
| `glass_shatter` | ASP / Nest detector | event-triggered; notify TODO (#97) |
| `CameraSound` | SDM `sdm.devices.traits.CameraSound` + Pub/Sub | ingest → detector |
| `CameraMotion` / `CameraPerson` | SDM traits | optional correlate |
| `CameraClipPreview` | `CameraClipPreview.ClipPreview` | session correlation; **URL never on public wire** |
| `CameraEventImage` | SDM trait | snapshot context stub only |

## Wire fields

Canonical: [`docs/api-contract.md`](../api-contract.md). Nest adds optional `nest*` keys and may set
existing `soundBurst` / `vibClass` / `alarmState` / `volBlast` via advisory hints — never under
`holdManual`. Detector labels: `glass_shatter` \| `sound_burst` \| `other`
(`iot_asp_autoroute/nest/detector.py`).

## Clamps / safety

- Hold / Manual clears blast escalation and refuses remote patch apply.
- No OAuth tokens, refresh tokens, or Device Access UUIDs in git / `.vv` / public telemetry.
- Clip preview URLs and raw device ids stay private (`meta/nest/` / memory only).
- Metered Gemini / `gcloud services enable --apply` require owner confirmation.

## Acceptance tests

| ID | Check |
|----|--------|
| PM-01 | This matrix lists all three surfaces + six hardware rows + six event classes |
| PM-02 | Each live cell names an owning issue or parked gate |
| PM-03 | Links resolve to `docs/nest-device-access.md` + `docs/api-contract.md` |
| PM-04 | Offline Nest tests still pass: `pytest tests/test_nest_events.py tests/test_nest_sdm.py -q` |

Checklist evidence: [`.vv/100/CHECKLIST.md`](../../.vv/100/CHECKLIST.md).

## CI gate

Docs + existing Nest offline pytest (no live SDM). Presence of this spec is the #100 Done signal for
the documentation cell; HW/live cells stay open until owner evidence.

## Risks / HW limits

- SDM never delivers audio bytes on CameraSound — classification is signal + phone `micDiff` fusion.
- Proprietary GoogleHomeSDK / Nest premium linking / console login are owner-only.
- Apple Home (#15) ≠ Google Nest — do not conflate in this matrix.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/100
- https://developers.google.com/nest/device-access/api
- https://developers.google.com/nest/device-access/traits
- https://developers.google.com/nest/device-access/traits/device/camera-sound
- https://developers.google.com/nest/device-access/traits/device/camera-clip-preview
- https://developers.home.google.com/apis/ios/get-started
- [`docs/nest-device-access.md`](../nest-device-access.md)
- [`docs/api-contract.md`](../api-contract.md)
