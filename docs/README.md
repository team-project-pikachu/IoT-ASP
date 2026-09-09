# IoT-ASP docs

[![Awesome](https://awesome.re/badge-flat.svg)](https://awesome.re)

**Start here.** One index for the hop fleet (phones → Soundcore, control plane on GCP/ADK).  
Skim this page, then open one link below. Do not hunt through `docs/issues/` or `docs/specs/` first.

## What this product is (30 seconds)

Three phones blast near-ultrasound (17–23 kHz) over **system Bluetooth** to Soundcore speakers.  
The browser/PWA only plays audio and polls a **patch** file. Gemini/ADK lives on the backend — no API keys in the page.

Hard rule: **phone → speaker = native A2DP** (not Web Bluetooth). Details: [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md).

## Start here path

| If you need… | Open |
|--------------|------|
| What we’re building | [PRD.md](PRD.md) |
| What’s next / order of work | [roadmap.md](roadmap.md) |
| How the PWA + backend split | [architecture-pwa.md](architecture-pwa.md) |
| Field acceptance | [UAT.md](UAT.md) |
| CI / verify vs validate | [TESTING_PLAN.md](TESTING_PLAN.md) |
| Telemetry + patch JSON | [api-contract.md](api-contract.md) |

Live app: see repo [README](../README.md). Board: [Project 5](https://github.com/orgs/team-project-pikachu/projects/5).

## Contents

1. [Vision & product](#1-vision--product)
2. [Architecture & API](#2-architecture--api)
3. [Surfaces](#3-surfaces)
4. [Ops & ship](#4-ops--ship)
5. [Science & prior art](#5-science--prior-art)
6. [Archive & deep dives](#6-archive--deep-dives)
7. [Contributing to docs](#7-contributing-to-docs)

---

## 1. Vision & product

| Doc | One-liner |
|-----|-----------|
| [PRD.md](PRD.md) | Goals, non-goals, FRs by surface |
| [roadmap.md](roadmap.md) | Milestones = iOS / macOS / Nest / Sonos / Platform |
| [UAT.md](UAT.md) | Human acceptance checklists |
| [TESTING_PLAN.md](TESTING_PLAN.md) | SEBoK verify vs validate; CI evidence |
| [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) | C1–C6 (A2DP, band, power, …) |
| [mvp-closed-log.md](mvp-closed-log.md) | Closed-issue history |
| [mvp-roadmap.md](mvp-roadmap.md) | Stub → points at roadmap |

## 2. Architecture & API

| Doc | One-liner |
|-----|-----------|
| [architecture-pwa.md](architecture-pwa.md) | Vercel `public/` vs GCP/ADK; Hold/Manual |
| [api-contract.md](api-contract.md) | `schemaVersion: 1` telemetry + patch |
| [autoroute.md](autoroute.md) | suddenFreq → rotate loop |
| [adk-autoroute.md](adk-autoroute.md) | ADK agent package / Cloud Run |
| [gemini-enterprise.md](gemini-enterprise.md) | Engine `iot-asp-autoroute` |
| [test-traceability.md](test-traceability.md) | Closed issues → tests |

## 3. Surfaces

| Surface | Docs |
|---------|------|
| **iOS / iPhone** | [iphone-bluetooth.md](iphone-bluetooth.md) · [iphone-dedicated-mode.md](iphone-dedicated-mode.md) · [native-xcode.md](native-xcode.md) · [sensors-chrome-ios.md](sensors-chrome-ios.md) · [sensorkit-watch.md](sensorkit-watch.md) |
| **macOS / PWA** | [architecture-pwa.md](architecture-pwa.md) · live URL in root README |
| **Nest** | [nest-device-access.md](nest-device-access.md) |
| **Sonos** | [sonos-beam.md](sonos-beam.md) · [sonos-beam-gen2-airplay-volume-constraints.md](sonos-beam-gen2-airplay-volume-constraints.md) (AirPlay click/clip/**static**) |
| **Hardware** | [hardware/soundcore-2.md](hardware/soundcore-2.md) · [hardware/soundcore-specs.md](hardware/soundcore-specs.md) · [connectivity-wifi.md](connectivity-wifi.md) · [power-fleet.md](power-fleet.md) |

## 4. Ops & ship

| Doc | One-liner |
|-----|-----------|
| [ci.md](ci.md) | Required CI jobs |
| [deploy.md](deploy.md) | Actions → Vercel dev/test/prod |
| [branch-protection.md](branch-protection.md) | Main ruleset |
| [vercel-webhooks.md](vercel-webhooks.md) | Deploy notifications (#37) |
| [vv/README.md](vv/README.md) | SEBoK evidence layout |
| [accounts-and-seats.md](accounts-and-seats.md) | Seats / accounts (no secrets) |
| [gcp-recordings.md](gcp-recordings.md) | Recording bucket notes |

## 5. Science & prior art

| Doc | One-liner |
|-----|-----------|
| [algorithms.md](algorithms.md) | Carrier / hop modes |
| [physics.md](physics.md) | Seismo-acoustic priors |
| [materials-engineering.md](materials-engineering.md) | Material ↔ vib channel |
| [timestore.md](timestore.md) · [timestore-scipy.md](timestore-scipy.md) | Timestore fit package |
| [asp-prior-art.md](asp-prior-art.md) | Awesome-list + .gov + USPTO process |
| [awesome-list-asp.md](awesome-list-asp.md) | Short search cheat-sheet |
| [similar-projects.md](similar-projects.md) | Related OSS |
| [PRIOR_ART.md](PRIOR_ART.md) | Decision register for shipped tooling |

External hubs: [awesome-list topic](https://github.com/topics/awesome-list) · [faroit/awesome-python-scientific-audio](https://github.com/faroit/awesome-python-scientific-audio) · [nitnelav/awesome-acoustic](https://github.com/nitnelav/awesome-acoustic).

## 6. Archive & deep dives

| Kind | Links |
|------|-------|
| Feature specs | [specs/README.md](specs/README.md) |
| Issue mirrors | [issues/](issues/) (historical; use GitHub for source of truth) |
| UX notes | [ux-tooling.md](ux-tooling.md) · [ux-provenance.md](ux-provenance.md) · [wireframe-notes.md](wireframe-notes.md) |
| Colab / tooling | [colab-gemini-pipeline.md](colab-gemini-pipeline.md) · [mvp-tooling.md](mvp-tooling.md) · [dependencies.md](dependencies.md) |
| Checklists | [well-architected-ai.md](well-architected-ai.md) · [sdd-app-control.md](sdd-app-control.md) · [notion-links.md](notion-links.md) |
| Parked / edge | [ai-edge-portal.md](ai-edge-portal.md) · [multi-llm-registry.md](multi-llm-registry.md) · [sensorkit-research-closeout.md](sensorkit-research-closeout.md) |
| Study / rules | [STUDY_PRIVATE.md](STUDY_PRIVATE.md) · [rules-index.md](rules-index.md) · [mdc-conversion.md](mdc-conversion.md) |
| Redirect stub | [awesome-iot-asp.md](awesome-iot-asp.md) → this README |

## 7. Contributing to docs

1. Put durable product truth in the canon table under **Start here** — not a new top-level essay.
2. Add a **TL;DR** (3–5 lines) at the top of any doc humans open often.
3. Link new files from **this** README or they show as orphans in CI.
4. Run locally: `python3 scripts/docs_analyzer.py` (broken links fail; orphans/size/readability warn).
5. Prefer stubs that point at a canonical file over duplicating long tables.

Analyzer knobs: `DOCS_ANALYZER_FAIL_ON` (`broken_links` default), `DOCS_ANALYZER_LINE_THRESHOLD` (400), `DOCS_ANALYZER_PARA_WORDS` (120). Workflow: `.github/workflows/docs-analyzer.yml`.
