# #19 — Notion hub page for ASP tooling (if missing)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/19 · Labels: `parked`, `docs` · Related: `docs/notion-links.md`, `docs/awesome-iot-asp.md`, `docs/STUDY_PRIVATE.md`

## Status

**Hub created 2026-09-08.** Public-safe Notion page [IoT-ASP — Adaptive Signal Processing hub](https://www.notion.so/IoT-ASP-Adaptive-Signal-Processing-hub-3d5bf46958418109a303eb31342ff50d)
exists (page id `3d5bf469-5841-8109-a303-eb31342ff50d`). This PR back-links it from `docs/notion-links.md`
and `docs/awesome-iot-asp.md`. Remaining work is **optional** (ASP docs database + `notion_hub_sync.py`);
do **not** create a second hub page.

The 2026-09-07 Notion MCP search is kept as history: no relevant pages or databases were found then
(one false positive), so the "if missing" condition of the issue was met.

## Goal

A durable **Notion hub** for ASP / Gemini / scientific tooling that (1) deep-links the public GitHub docs
(generic only), (2) is itself linked from `docs/awesome-iot-asp.md` and `docs/notion-links.md`, (3) keeps
every site-specific item (addresses, room names, recording URIs, seat emails) in the **private**
`IoT-ASP-study` tree, never on the public hub, and (4) prefers linking existing pages over duplicating.

## Prior art

Checked 2026-09-08. Reuse the existing public index and the already-created hub; do not fork a second
workspace page or invent a token.

| What already exists | Where | Decision |
|---------------------|-------|----------|
| Keyword search log (2026-09-07): `notion-search`; `notion-ai-search` needs Business plan; **no relevant hits**; one Work Tale false positive | `docs/notion-links.md` | Keep as history; do not treat the empty result as current |
| Public curated index the hub mirrors (constraints, control plane, science, KB, edge, privacy) | `docs/awesome-iot-asp.md` | Hub links GitHub paths; GitHub remains source of truth |
| Spec outline for this issue (page sections, public/private split, optional API) | this file, landed on `main` earlier | Status only — hub is now created |
| Private-study pointer | `docs/STUDY_PRIVATE.md`; gitignored `study/` | Keep site protocol out of the hub |
| Gemini Enterprise Notion connector (data-store ingest) | Google Cloud Gemini Enterprise docs | Out of scope; not a substitute for a human-readable hub |
| Notion API: pages parented on `page_id` / `data_source_id`; classic `POST /v1/databases` deprecated as of 2025-09-03 | Context7 `/websites/developers_notion_reference` | Optional DB/sync only; pin `Notion-Version` if a script is added later |

**Why a hub instead of linking an existing page:** the 2026-09-07 search found none. **Why not a
database first:** issue #19 asked for a hub page; a database is optional follow-up. **Why not
`scripts/notion_hub_sync.py` in this PR:** optional; requires `NOTION_TOKEN` (name only in git) and
must never run in CI.

## Shipped on `main`

Verified by reading the files (`origin/main` @ `7eb8caf`) plus the live hub (Notion fetch 2026-09-08):

| What | Where |
|------|-------|
| Hub page (title "IoT-ASP — Adaptive Signal Processing hub"; Live & source / Constraints / Control plane / Science / Edge / Private; no site PII) | [notion.so](https://www.notion.so/IoT-ASP-Adaptive-Signal-Processing-hub-3d5bf46958418109a303eb31342ff50d) |
| Hub URL in Relevant hits (`notion.so`, no `token` query) | `docs/notion-links.md` § Relevant hits |
| 2026-09-07 search log kept as history | `docs/notion-links.md` § Search log (2026-09-07) |
| Knowledge Base back-link to the same URL | `docs/awesome-iot-asp.md` § Knowledge Base |
| Private-study pointer (companion `IoT-ASP-study`; `study/` gitignored) | `docs/STUDY_PRIVATE.md`; `CLAUDE.md` invariant 7 |
| Secrets-by-name rule (1Password `dev`, GitHub secrets, Colab `userdata`, Secret Manager) | `CLAUDE.md` invariant 10 |
| Docs rule: public docs stay generic; site protocol lives in `study/` | `.claude/rules/docs-and-specs.md:16` |

## Remaining scope

Hub page and repo back-links are done. Optional follow-up only:

1. **Optional database** "ASP docs" with properties `Name` (title), `Area` (select: constraints / control
   plane / science / edge / ops), `Public` (checkbox), `GitHub path` (url), `Issue` (number) — one row per
   `docs/*.md` and per spec. If created by API, use a **data source** parent (the classic
   `POST /v1/databases` is deprecated as of API version 2025-09-03).
2. **Optional automation** `scripts/notion_hub_sync.py` (stdlib `urllib`, secret **name** `NOTION_TOKEN`):
   reads `docs/specs/README.md`'s index table and upserts rows into the database via `POST /v1/pages` with
   `parent: {data_source_id}` (or `database_id` on older versions), headers `Authorization: Bearer …` and
   `Notion-Version: 2026-03-11`. Dry-run by default (`--apply` to write); never run in CI. Do not invent
   a token value.
3. Privacy gate before any hub edit: run `fleet_log.is_pii_key` / `scrub_pii` over the rows and grep the
   page text for street-address patterns (`\d+ [A-Z][a-z]+ (St|Ave|Rd|Dr|Ln|Ct)\b`) and `@` addresses.

## Wire fields

None — documentation only. The telemetry/patch contract is unaffected.

## Clamps / safety

- **No site PII** on any page reachable from the public hub (addresses, neighbour identifiers, recording
  URIs, speech transcripts, seat emails). Private pages live under the study workspace and are linked with
  a "(private)" label only.
- Secrets by name: `NOTION_TOKEN` (internal integration), stored in 1Password `dev` / Colab `userdata`;
  never in git, chat, or issues. The integration needs only *Insert content* + *Read content* on the hub
  page — grant nothing else.
- Public docs remain the source of truth; the hub links to GitHub paths (`main` branch), it does not
  restate contract tables (`docs/api-contract.md` is canonical — rule `docs-and-specs.md:13`).
- Link existing pages rather than duplicating (`notion-links.md` Notes).

## Acceptance tests

Docs-level checks (manual or via the optional script's `--check` mode):

1. `docs/notion-links.md` § Relevant hits contains exactly one hub row with a `notion.so` / `notion.site`
   URL and no query string containing `token`.
2. `docs/awesome-iot-asp.md` § Knowledge Base links the same URL.
3. Every GitHub link on the hub resolves on `origin/main` (reuse the link-checker in
   `docs/specs/README.md` § Known missing docs; Mac-only docs are linked as "(pending on main)").
4. PII grep over the exported hub markdown (address regex + `@`) → no matches.
5. If the database exists: every `docs/specs/*.md` has a row; `Public` is checked for all of them;
   `Issue` matches the spec's issue number.
6. `scripts/notion_hub_sync.py --dry-run` exits 0 offline and prints the rows it *would* upsert (no
   network unless `--apply`). Optional; not shipped in this PR.

## CI gate

None (docs). `docs/ci.md` § Out of scope excludes heavy crawls; the sync script is never invoked by CI.

## Risks / HW limits

- `notion-ai-search` needs a Business plan; page search (`notion-search`) is what found "nothing", so the
  negative result is only as good as keyword search — check again before creating a duplicate.
- The Notion API version line moves (data sources replaced classic databases in 2025-09); pin
  `Notion-Version` in the script and expect to bump it.
- A public share link is public: the hub must be written as if it will be indexed.

## Sources

- GitHub issue #19 (read via the GitHub connector, 2026-09-08).
- Live hub fetch (Notion MCP `notion-fetch`, 2026-09-08): title matches; sections Live & source /
  Constraints / Control plane / Science / Edge / Private; no street addresses or seat emails.
- Context7 `/websites/developers_notion_reference` — Authentication (`Authorization: Bearer`,
  `Notion-Version` header required, example version `2026-03-11`); `POST /v1/pages` (parent `page_id` /
  `database_id` / `data_source_id` / `workspace`; requires Insert Content capability; 403 without it;
  optional `markdown` body and `allow_async`); `POST /v1/databases` deprecated as of version 2025-09-03.
- Repo: `docs/notion-links.md`, `docs/awesome-iot-asp.md`, `docs/STUDY_PRIVATE.md`, `.claude/rules/docs-and-specs.md`,
  `CLAUDE.md` (invariants 7, 10).
