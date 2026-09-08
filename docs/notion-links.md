# Notion workspace links — IoT-ASP context

**Hub created:** 2026-09-08 for [GitHub issue #19](https://github.com/team-project-pikachu/IoT-ASP/issues/19)  
**Search date:** 2026-09-07  
**Tool:** Notion MCP (`notion-search`; `notion-ai-search` unavailable — requires Business plan)  
**Queries:** IoT-ASP, Gemini Enterprise, ultrasonic, adaptive signal processing, Soundcore, study/lab, hop ultrasonic, bear-iot-asp, SensorKit, autoroute Gemini, scientific tooling ASP

## Relevant hits

| Title | Type | One-line | Link |
|-------|------|----------|------|
| IoT-ASP — Adaptive Signal Processing hub | page | Durable public hub for ASP / Gemini / scientific tooling. Created 2026-09-08 for #19. Generic only — no site PII. | [notion.so](https://www.notion.so/IoT-ASP-Adaptive-Signal-Processing-hub-3d5bf46958418109a303eb31342ff50d) |

## Search log (2026-09-07)

Keyword search on 2026-09-07 found **no relevant pages or databases** for IoT-ASP / ultrasonic ASP / Gemini Enterprise / Soundcore / study-lab tooling (one false positive below). That negative result is why the hub was created the next day rather than linking an existing page.

## Non-relevant / false positives

| Title | Type | One-line | Link |
|-------|------|----------|------|
| Work Tale — frontend architecture + data plane | page | Unrelated Work Tale notes; matched keyword fragments (“process” / “tools”), not ASP. | [Notion](https://app.notion.com/p/3d0bf4695841811398f9d4b4c1e4c2dc?pvs=204) |

## Follow-up

Hub exists; do **not** create a second page. Prefer linking this hub over duplicating. Remaining work is optional (not required to close #19):

- Notion database “ASP docs” (data-source parent; classic `POST /v1/databases` is deprecated)
- `scripts/notion_hub_sync.py` (secret **name** `NOTION_TOKEN` only — never invent a value)

Already tracked:

- GitHub: [Issue #19 — Notion hub page for ASP tooling (if missing)](https://github.com/team-project-pikachu/IoT-ASP/issues/19)

## Notes

- Public docs must stay scrubbed of study-site addresses; site-specific protocol stays in private `IoT-ASP-study`.
- Prefer linking existing Notion pages over duplicating once a hub exists.
- Public docs use the `notion.so` URL (no query tokens).
