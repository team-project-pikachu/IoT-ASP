# Awesome IoT-ASP

Curated index for the public Adaptive Signal Processing hop fleet.

## Live

- Blaster PWA (Vercel): see repo README  
- Source: `public/index.html`

## Control plane

- [Gemini Enterprise (5 seats, hybrid)](gemini-enterprise.md) — engine **`iot-asp-autoroute`**
- [ADK autoroute agent](adk-autoroute.md) — Agent Development Kit on Agent Platform  
  Overview: https://docs.cloud.google.com/agent-builder/agent-development-kit/overview
- [Autoroute telemetry + patches](autoroute.md)
- [Colab ↔ Gemini pipeline](colab-gemini-pipeline.md)

## Algorithms & physics

- [Carrier algorithms (EE)](algorithms.md)
- [Physics priors (NS / seismo-acoustic)](physics.md)
- [Literature](../reference/LITERATURE.md)

## Knowledge Base

- Living KB: [`reference/knowledge-base/`](../reference/knowledge-base/README.md)
- Refresh: `bash scripts/kb_refresh.sh`
- Context7 caches: `.context7/` (gitignored)
- Firecrawl ingest (vibration / ADK): [`reference/knowledge/INGEST.md`](../reference/knowledge/INGEST.md), [`reference/knowledge/adk/`](../reference/knowledge/adk/)

## Edge (parked — GitHub Issues)

- Raspberry Pi 5 field node  
- Apple Home / HomeKit / Matter  
- SensorKit (native) expansions  
- Multi-LLM autoroute registry (post-Gemini)

## Privacy

- Private study protocol: local `study/` (gitignored). Pointer: [STUDY_PRIVATE.md](STUDY_PRIVATE.md)
