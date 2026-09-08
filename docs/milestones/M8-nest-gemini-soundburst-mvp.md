# M8 — Nest cameras + Gemini sound-burst + glass shatter MVP

**Milestone:** [M8 — Nest cameras + Gemini sound-burst MVP](https://github.com/team-project-pikachu/IoT-ASP/milestone/9)  
**Owner identity (Google Home / Nest premium + GCP):** `betty@bearresearch.io`  
**Home APIs iOS get-started:** https://developers.home.google.com/apis/ios/get-started  
**Native app:** [`native/IoTASPHome/`](../../native/IoTASPHome/) (second first-class iOS feature beside [`native/IoTASP`](../../native/IoTASP/))

## Architecture (sketch)

```text
Nest cam mic / ASP micDiff features
        │
        ▼
 AcousticEventFeatures ──► BurstDetectClient (stub | Gemini Enterprise via gcloud/Vertex)
        │                         │
        │                    eventClass:
        │                    sound_burst | glass_shatter | unknown
        ▼
 EscalatingAlarmController ──► louder over time (volBlast / alarmState concepts)
        │
        ├── HomeNestAlarm UI tab
        ├── Glass Shatter UI tab (event-triggered notify TODO)
        └── NestCameraCatalog snapshot context stub
```

## First-class app features

| Feature | Module | Notes |
|---------|--------|-------|
| ASP Ultrasonic (sibling) | `native/IoTASP` | Existing hop / impulse shell |
| HomeNestAlarm | `HomeNestAlarm` + UI tab | Nest cameras + sound-burst → escalate |
| Glass Shatter | `GlassShatterPipeline` + UI tab | Event-triggered; shares detector enum |

## Owner-gated steps (agents cannot do)

1. Google Home Developer Console — register app / OAuth as **betty@bearresearch.io**
2. Nest premium device linking on that account
3. GCP project select + `gcloud auth` as owner; enable paid/Gemini Enterprise APIs only after confirmation
4. Place OAuth client / API keys in 1Password `dev` (names only in git)
5. Live GoogleHomeSDK SPM/CocoaPods binary + Xcode.app device run

## Agent Did / Didn’t

| Did | Didn’t |
|-----|--------|
| Milestone + issues + this doc | Browser login / Nest console auth-wall scrape |
| `native/IoTASPHome` stub that `swift build`s | Vendored proprietary GoogleHomeSDK |
| `scripts/home_ios_build.sh` / `make home-ios-build` | Live OAuth or Nest token mint |
| `scripts/home_apis_gcloud_bootstrap.sh` dry-run | `--apply` / paid API enable without confirmation |
| `services/gemini-burst-detect` heuristic stub | Metered Gemini calls |
| Glass shatter event class + pipeline stub | Real shatter ML model training |
| Cross-link #15 (Apple Home ≠ Google Home) | Conflate HomeKit with Nest |
| Firecrawl CLI public Nest/Home docs → `reference/nest-device-access/` | Authenticated console browse / OAuth mint |

## Pending outside this pass

- #101 PWA `eventClass` / glass_shatter UI and #102 Playgrounds workflow (honest pending; specs stubbed)

## Specs + evidence (this pass)

- Per-issue specs: `docs/specs/83-*.md` … `docs/specs/104-*.md` (index in `docs/specs/README.md`)
- Fresh evidence: [`.vv/m8/EVIDENCE.md`](../../.vv/m8/EVIDENCE.md) (UTC procedure, exit codes, pass/fail; no secrets)

## Build proof

```bash
make home-ios-build
# or: bash scripts/home_ios_build.sh
# evidence refresh: see .vv/m8/EVIDENCE.md
```

## gcloud surfaces (names)

- `gcloud ai` / `gcloud beta ai` / `gcloud alpha ai` — Vertex AI entity management  
- `gcloud services enable aiplatform.googleapis.com` — only with `--apply` after owner OK  
- Home APIs OAuth remains console-side (not solely a services enable)

## Related issues

| # | Title |
|--:|-------|
| [#83](https://github.com/team-project-pikachu/IoT-ASP/issues/83) | Home APIs iOS OAuth + SDK scaffold |
| [#84](https://github.com/team-project-pikachu/IoT-ASP/issues/84) | Nest camera discovery / Device API camera traits |
| [#85](https://github.com/team-project-pikachu/IoT-ASP/issues/85) | Premium Nest features checklist (betty@bearresearch.io) |
| [#86](https://github.com/team-project-pikachu/IoT-ASP/issues/86) | Audio/event path — Nest mic or ASP micDiff |
| [#87](https://github.com/team-project-pikachu/IoT-ASP/issues/87) | gcloud Gemini Enterprise burst detector stub |
| [#88](https://github.com/team-project-pikachu/IoT-ASP/issues/88) | Reactive alarm escalation (louder) |
| [#89](https://github.com/team-project-pikachu/IoT-ASP/issues/89) | E2E MVP acceptance |
| [#90](https://github.com/team-project-pikachu/IoT-ASP/issues/90) | Security/privacy |
| [#91](https://github.com/team-project-pikachu/IoT-ASP/issues/91) | App scaffold + stub build |
| [#92](https://github.com/team-project-pikachu/IoT-ASP/issues/92) | gcloud bootstrap + CI dry-check |
| [#93](https://github.com/team-project-pikachu/IoT-ASP/issues/93) | OAuth consent owner steps |
| [#94](https://github.com/team-project-pikachu/IoT-ASP/issues/94) | Camera device type integration stub |
| [#95](https://github.com/team-project-pikachu/IoT-ASP/issues/95) | Glass shatter — discovery |
| [#96](https://github.com/team-project-pikachu/IoT-ASP/issues/96) | Glass shatter — model/event class |
| [#97](https://github.com/team-project-pikachu/IoT-ASP/issues/97) | Glass shatter — Home app wiring |
| [#98](https://github.com/team-project-pikachu/IoT-ASP/issues/98) | Glass shatter — E2E acceptance |
| [#99](https://github.com/team-project-pikachu/IoT-ASP/issues/99) | Glass shatter — privacy / consent |

| [#100](https://github.com/team-project-pikachu/IoT-ASP/issues/100) | Platform matrix — Vercel / iOS / Playground × hardware × SDM |
| [#101](https://github.com/team-project-pikachu/IoT-ASP/issues/101) | Vercel PWA Nest/SDM + glass_shatter UI — **pending** (not in this PR) |
| [#102](https://github.com/team-project-pikachu/IoT-ASP/issues/102) | Swift Playground HomeNestAlarm stub — **pending** (`swift build` only here) |
| [#103](https://github.com/team-project-pikachu/IoT-ASP/issues/103) | SDM CameraSound + Pub/Sub → Gemini → louder alarm |
| [#104](https://github.com/team-project-pikachu/IoT-ASP/issues/104) | Hardware ladder Nest cams / doorbell / mic / Sonos |

## Knowledge ingest

- `reference/nest-device-access/KNOWLEDGE-INGEST.md` (Firecrawl CLI; console not scraped)

## Project board

- https://github.com/orgs/team-project-pikachu/projects/5 (IoT-ASP #5)

