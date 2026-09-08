# ISSUE-19 — Notion hub

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/19  
**Classification:** docs (hub created 2026-09-08)  
**Owner surface:** docs  
**Canonical spec / ADR:** `docs/specs/19-notion-hub.md`

## Scope (this pass)

Create a public-safe Notion hub if missing, then deep-link it from public docs. No site PII.

## Constraints

- No site PII in public docs.
- Do not invent secrets, entitlements, or HW capabilities.
- Prefer linking existing `docs/specs/` over forking tables (`docs/api-contract.md` is wire canon).
- Do not create a second Notion page.

## Did

- Hub page already exists: [IoT-ASP — Adaptive Signal Processing hub](https://www.notion.so/IoT-ASP-Adaptive-Signal-Processing-hub-3d5bf46958418109a303eb31342ff50d) (created 2026-09-08 for #19).
- Back-linked from `docs/notion-links.md` (Relevant hits) and `docs/awesome-iot-asp.md` (Knowledge Base).
- Spec status + Prior art updated; 2026-09-07 search log kept as history.

## Didn't

- Did not create a second Notion page.
- Did not add `scripts/notion_hub_sync.py` or an ASP docs database.
- Did not invent `NOTION_TOKEN` values.
- Did not copy study-site protocol, addresses, recording URIs, or seat emails into public docs.

## Next

- Optional: Notion database “ASP docs” + sync script (secret name only).
- Keep public docs generic; private protocol stays in `IoT-ASP-study`.
