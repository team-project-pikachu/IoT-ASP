# M8 — Nest cameras + Gemini sound-burst + glass shatter MVP

**Milestone:** [M8 — Nest cameras + Gemini sound-burst MVP](https://github.com/team-project-pikachu/IoT-ASP/milestone/9)
**Native app:** [`native/IoTASPHome/`](../../native/IoTASPHome/) (second first-class iOS feature beside [`native/IoTASP`](../../native/IoTASP/))
**This PR:** independent slice onto `main` — HomeNestAlarm SPM stub + Gemini burst detector stub. Does **not** include stacked PWA / balanced-docs churn.

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

Python stub JSON keys match Swift `AcousticDetectResult`: `burst`, `eventClass`, `confidence`, `escalateDb`.

## First-class app features

| Feature | Module | Notes |
|---------|--------|-------|
| ASP Ultrasonic (sibling) | `native/IoTASP` | Existing hop / impulse shell |
| HomeNestAlarm | `HomeNestAlarm` + UI tab | Nest cameras + sound-burst → escalate |
| Glass Shatter | `GlassShatterPipeline` + UI tab | Event-triggered; shares detector enum |

## Owner-gated steps (agents cannot do)

1. Google Home Developer Console — register app / OAuth as **bettyctai@gmail.com**
2. Nest premium device linking on that account
3. GCP project select + `gcloud auth` as owner; enable paid/Gemini Enterprise APIs only after confirmation
4. Place OAuth client / API keys in 1Password `dev` (names only in git)
5. Live GoogleHomeSDK SPM/CocoaPods binary + Xcode.app device run

Do **not** scrape `console.nest.google.com`. Do not mint or commit Nest/OAuth tokens.

## Agent Did / Didn’t

| Did | Didn’t |
|-----|--------|
| `native/IoTASPHome` stub that `swift build`s without GoogleHomeSDK | Vendored proprietary GoogleHomeSDK |
| `scripts/home_ios_build.sh` / `make home-ios-build` | Live OAuth or Nest token mint |
| `scripts/home_apis_gcloud_bootstrap.sh` dry-run by default | `--apply` / paid API enable without confirmation |
| `services/gemini-burst-detect` heuristic stub (no metered Gemini) | Metered Gemini / Vertex live calls |
| Glass shatter event class + `EscalatingAlarmController` (louder while sustaining) | Real shatter ML model training |
| Linux CI presence check for `Package.swift` + Python stub pytest | `swift build` on ubuntu-latest (macOS-only) |
| Cross-link #15 (Apple Home ≠ Google Home) | Conflate HomeKit with Nest |

## Build proof

```bash
make home-ios-build                 # macOS, Swift toolchain; stub mode (no GoogleHomeSDK)
bash scripts/home_apis_gcloud_bootstrap.sh   # dry-run; exit 0; no mutations
python3 -m pytest tests/test_gemini_burst_detect.py -q
```

`make home-ios-build` is **macOS-only**. Linux CI job `M8 Home iOS stub presence` checks files + runs the Python detector tests; it does not invoke Swift.

## gcloud surfaces (names)

- `gcloud ai` / `gcloud beta ai` / `gcloud alpha ai` — Vertex AI entity management
- `gcloud services enable aiplatform.googleapis.com` — only with `--apply` after owner OK
- Home APIs OAuth remains console-side (not solely a services enable)

## Related issues (this slice)

| # | Title | This PR |
|--:|-------|---------|
| [#91](https://github.com/team-project-pikachu/IoT-ASP/issues/91) | App scaffold + stub build | SPM stub + `#if canImport(GoogleHomeSDK)` |
| [#87](https://github.com/team-project-pikachu/IoT-ASP/issues/87) | gcloud Gemini Enterprise burst detector stub | `services/gemini-burst-detect` |
| [#96](https://github.com/team-project-pikachu/IoT-ASP/issues/96) | Glass shatter — model/event class | `AcousticEventClass` `glass_shatter` |
| [#88](https://github.com/team-project-pikachu/IoT-ASP/issues/88) | Reactive alarm escalation (louder) | `EscalatingAlarmController` |
| [#102](https://github.com/team-project-pikachu/IoT-ASP/issues/102) | Swift Playground HomeNestAlarm stub | `swift build` only here (Playgrounds pending) |
| [#90](https://github.com/team-project-pikachu/IoT-ASP/issues/90) | Security/privacy | scopes + recording consent in `native/IoTASPHome/README.md` |
| [#92](https://github.com/team-project-pikachu/IoT-ASP/issues/92) | gcloud bootstrap + CI dry-check | dry-run script + linux presence job |

Related, not fully implemented here: #89 #98 #97 (E2E / Home wiring), #83–#86 #93–#95 #99–#101 #103–#104 (OAuth live SDK, PWA UI, SDM Pub/Sub, hardware ladder).

## Specs

- [`docs/specs/87-gemini-burst-detector-stub.md`](../specs/87-gemini-burst-detector-stub.md)

## Project board

- https://github.com/orgs/team-project-pikachu/projects/5 (IoT-ASP #5)
