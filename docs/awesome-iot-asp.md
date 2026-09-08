# Awesome IoT-ASP

Curated index for the public Adaptive Signal Processing hop fleet.

## Live

- Blaster PWA (Vercel): see repo README
- Source: `public/index.html`

## Awesome-list / prior art first (ASP)

- Topic: https://github.com/topics/awesome-list
- Process: [asp-prior-art.md](asp-prior-art.md) · [awesome-list-asp.md](awesome-list-asp.md)
- Rule: `.cursor/rules/asp-prior-art.mdc` (Firecrawl + Context7 + .gov + USPTO)
- **Developer index:** [`.firecrawl/developer-index/INDEX.md`](../.firecrawl/developer-index/INDEX.md) (71 unique entries; SciPy / ADK / Web Audio / Vertex·Gemini / awesome DSP)
- Awesome hubs: [faroit/awesome-python-scientific-audio](https://github.com/faroit/awesome-python-scientific-audio) · [nitnelav/awesome-acoustic](https://github.com/nitnelav/awesome-acoustic)

## Context7 baselines (library docs)

| Library ID | Concept | Use in ASP |
|------------|---------|------------|
| `/scipy/scipy` | `signal.welch` · `optimize.curve_fit` | Vib PSD / timestore nonlinear fits |
| `/google/adk-python` | `LlmAgent` + `adk deploy agent_engine` | Autoroute agent |
| `/websites/webaudio_github_io_web-audio-api` | `AudioContext` / Gain / Oscillator | Hop blaster TX graph |

Caches under `.context7/` (see [asp-prior-art.md](asp-prior-art.md)).

## Design constraints (formal)

- [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) — **C1** native A2DP · **C2** Pi USB-C (#14) · **C3** SDD · **C4** max gain · **C5** 120 V AC · **C6** LF 10–20 Hz gated
- [power-fleet.md](power-fleet.md) — continuous **120 V AC**
- [SEBoK V&V](vv/README.md) · [`.vv/matrix.md`](../.vv/matrix.md) — Req IDs → issues #12/#16/#17/#9/#13
- [iphone-dedicated-mode.md](iphone-dedicated-mode.md)
- [iphone-bluetooth.md](iphone-bluetooth.md)
- [timestore.md](timestore.md) · [ai-edge-portal.md](ai-edge-portal.md) (parked)

## Control plane

- [API contract](api-contract.md) — telemetry / patch JSON + `schemaVersion` (frontend polls only)
- [Gemini Enterprise (5 seats, hybrid)](gemini-enterprise.md) — engine **`iot-asp-autoroute`**
- [ADK autoroute agent](adk-autoroute.md) — independent Cloud Run deploy; https://docs.cloud.google.com/agent-builder/agent-development-kit/overview
- [Autoroute: suddenFreq → Gemini autorotate](autoroute.md)
- [Colab ↔ Gemini pipeline](colab-gemini-pipeline.md)
- [MVP tooling (verified pins)](mvp-tooling.md)
- [Well-Architected AI checklist](well-architected-ai.md)

## Algorithms, physics, materials

- [Carrier algorithms (EE)](algorithms.md)
- [Physics priors (NS / seismo-acoustic)](physics.md)
- [Materials engineering](materials-engineering.md)
- [Literature](../reference/LITERATURE.md)
- [Similar OSS projects](similar-projects.md)

## UX (adapt, don’t invent)

- [UX tooling (Chrome + HIG)](ux-tooling.md)
- [UX provenance](ux-provenance.md)
- [Wireframe notes](wireframe-notes.md)
- [Native Xcode path](native-xcode.md)

## Knowledge Base

- Living KB: [`reference/knowledge-base/`](../reference/knowledge-base/README.md)
- **Notion hub:** [IoT-ASP — Adaptive Signal Processing hub](https://www.notion.so/IoT-ASP-Adaptive-Signal-Processing-hub-3d5bf46958418109a303eb31342ff50d) (public-safe; generic ASP / Gemini / scientific tooling — no site PII)
- Refresh: `bash scripts/kb_refresh.sh`
- Context7 caches: `.context7/` (gitignored)
- Firecrawl ingest: [`reference/knowledge/INGEST.md`](../reference/knowledge/INGEST.md)

## Edge (parked — GitHub Issues)

- Raspberry Pi 5 + **USB-C** (#14)
- Apple Home / HomeKit / Matter (#15) — not A2DP TX
- Google Home Wi‑Fi autorotate · cellular later (#21)
- SensorKit native shell (#9) — [sensorkit-research-closeout.md](sensorkit-research-closeout.md) (research Done-ready; impl parked)
- Timestore SciPy ≥16-param + weather/ciphers (#20)
- AI Edge Portal (#23) — [ai-edge-portal.md](ai-edge-portal.md)
- Multi-LLM autoroute registry (#13) — [multi-llm-registry.md](multi-llm-registry.md) (design sketch; no prod non-Gemini)
- Telemetry logging enrichment (#22)
- Missing ops note (later lane): `docs/gcp-recordings.md` (`bear-iot-asp-rec`)

## Privacy

- Private study protocol: companion `IoT-ASP-study`. Pointer: [STUDY_PRIVATE.md](STUDY_PRIVATE.md)
- **Glass shatter consent (#99):** [glass-shatter-privacy.md](glass-shatter-privacy.md) · [specs/99-glass-shatter-privacy.md](specs/99-glass-shatter-privacy.md) (live OAuth steps stay on parked #93)
