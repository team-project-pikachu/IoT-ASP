# Awesome IoT-ASP

Curated index for the public Adaptive Signal Processing hop fleet.

## Live

- Blaster PWA (Vercel): see repo README
- Source: `public/index.html`

## Design constraints (formal)

- [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) — **C1** native A2DP only · **C2** Pi USB-C (#14)
- [iphone-bluetooth.md](iphone-bluetooth.md)

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
- Refresh: `bash scripts/kb_refresh.sh`
- Context7 caches: `.context7/` (gitignored)
- Firecrawl ingest: [`reference/knowledge/INGEST.md`](../reference/knowledge/INGEST.md)

## Edge (parked — GitHub Issues)

- Raspberry Pi 5 + **USB-C** (#14)
- Apple Home / HomeKit / Matter (#15) — not A2DP TX
- SensorKit native shell (#9)
- Multi-LLM autoroute registry (post-Gemini)

## Privacy

- Private study protocol: companion `IoT-ASP-study`. Pointer: [STUDY_PRIVATE.md](STUDY_PRIVATE.md)
