# #19 — Notion hub evidence

**Date (UTC):** 2026-09-08T05:01:58Z  
**Revision:** `38b7e3b` (`docs/19-notion-hub`)  
**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/19

## Procedure

1. Confirm hub URL is public `notion.so` form without `token` query (docs only; no secrets).
2. Grep local public docs that back-link the hub for street-address + `@` patterns.
3. Record that live Notion page fetch (2026-09-08, Notion MCP `notion-fetch`) showed expected sections and no site PII.

## Observed results

| Check | Result | Notes |
|-------|--------|-------|
| Hub URL form | PASS | `https://www.notion.so/IoT-ASP-Adaptive-Signal-Processing-hub-3d5bf46958418109a303eb31342ff50d` (no query token) |
| Address regex on `docs/notion-links.md` + `docs/awesome-iot-asp.md` | PASS | matches=0 |
| Email `@` grep on same files | PASS | matches=0 |
| Live hub fetch (2026-09-08) | PASS | recorded in spec Sources; no street addresses / seat emails |

## Exit codes

- Local evidence authoring: exit `0` (docs-only; no CI gate for Notion network).

## Pass / fail

**PASS** for docs back-links + privacy grep on public repo docs. Live hub content re-check remains owner-gated if Notion auth expires.
