# #19 — Notion hub page for ASP tooling (if missing)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/19 · Labels: `parked`, `docs` · Related: `docs/notion-links.md`, `docs/awesome-iot-asp.md`, `docs/STUDY_PRIVATE.md`

## Status

**Parked — search done, hub not created.** `docs/notion-links.md` (2026-09-07) records that a Notion MCP
search for IoT-ASP / ultrasonic ASP / Gemini Enterprise / Soundcore / study-lab tooling found **no relevant
pages or databases** (one false positive), so the "if missing" condition of the issue is met. Creating the
hub is a docs task with no code; it is explicitly "not a blocker for Gemini autoroute v0". This spec fixes
the hub's structure, the public/private split, and the (optional) API automation so it can be done in one
sitting without leaking site PII.

## Goal

A durable **Notion hub** for ASP / Gemini / scientific tooling that (1) deep-links the public GitHub docs
(generic only), (2) is itself linked from `docs/awesome-iot-asp.md` and `docs/notion-links.md`, (3) keeps
every site-specific item (addresses, room names, recording URIs, seat emails) in the **private**
`IoT-ASP-study` tree, never on the public hub, and (4) prefers linking existing pages over duplicating.

## Shipped on `main`

Verified by reading the files (`origin/main` @ `0625e91`):

| What | Where |
|------|-------|
| Notion search log: tool `notion-search` (`notion-ai-search` unavailable — requires Business plan); queries listed; **no relevant hits**; one unrelated false positive | `docs/notion-links.md:3-17` |
| Follow-up already points at issue #19 and states the rules (no addresses / site PII; link, don't duplicate) | `docs/notion-links.md:19-29` |
| Curated public index that the hub mirrors (constraints, control plane, algorithms/physics, KB, edge, privacy) | `docs/awesome-iot-asp.md` |
| Private-study pointer (companion `IoT-ASP-study`; `study/` gitignored) | `docs/STUDY_PRIVATE.md`; `CLAUDE.md` invariant 7 |
| Secrets-by-name rule (1Password `dev`, GitHub secrets, Colab `userdata`, Secret Manager) | `CLAUDE.md` invariant 10 |
| Docs rule: public docs stay generic; site protocol lives in `study/` | `.claude/rules/docs-and-specs.md:16` |

## Remaining scope

1. **Hub page (manual, Notion UI or MCP `notion-create-pages`)** — title "IoT-ASP — Adaptive Signal
   Processing hub"; sections mirror `docs/awesome-iot-asp.md`:
   - *Live & source*: public app URL, repo, `docs/specs/README.md` (spec index).
   - *Constraints*: C1 (native A2DP), C2 (Pi USB-C) → `docs/DESIGN_CONSTRAINTS.md`.
   - *Control plane*: `docs/api-contract.md`, `docs/adk-autoroute.md`, `docs/autoroute.md`,
     `docs/gemini-enterprise.md` (engine id `iot-asp-autoroute`, credential **names** only).
   - *Science*: `docs/algorithms.md`, `docs/physics.md`, `reference/LITERATURE.md`.
   - *Edge (parked)*: links to the parked specs in `docs/specs/`.
   - *Private*: one line — "Site protocol, addresses and recordings: private `IoT-ASP-study` (request access)".
   Content is links + one-line summaries; **no** copied study text.
2. **Optional database** "ASP docs" with properties `Name` (title), `Area` (select: constraints / control
   plane / science / edge / ops), `Public` (checkbox), `GitHub path` (url), `Issue` (number) — one row per
   `docs/*.md` and per spec. If created by API, use a **data source** parent (the classic
   `POST /v1/databases` is deprecated as of API version 2025-09-03).
3. **Back-links in the repo** (docs-owned, this spec's follow-up PR): add the hub URL to
   `docs/notion-links.md` § Relevant hits and to `docs/awesome-iot-asp.md` § Knowledge Base. The URL is a
   public Notion share link with **no** embedded tokens.
4. **Optional automation** `scripts/notion_hub_sync.py` (stdlib `urllib`, secret name `NOTION_TOKEN`):
   reads `docs/specs/README.md`'s index table and upserts rows into the database via `POST /v1/pages` with
   `parent: {data_source_id}` (or `database_id` on older versions), headers `Authorization: Bearer …` and
   `Notion-Version: 2026-03-11`. Dry-run by default (`--apply` to write); never run in CI.
5. Privacy gate before publishing: run `fleet_log.is_pii_key` / `scrub_pii` over the rows and grep the
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
- Link existing pages rather than duplicating (`notion-links.md:29`).

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
   network unless `--apply`).

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
- Context7 `/websites/developers_notion_reference` — Authentication (`Authorization: Bearer`,
  `Notion-Version` header required, example version `2026-03-11`); `POST /v1/pages` (parent `page_id` /
  `database_id` / `data_source_id` / `workspace`; requires Insert Content capability; 403 without it;
  optional `markdown` body and `allow_async`); `POST /v1/databases` deprecated as of version 2025-09-03.
- Repo: `docs/notion-links.md`, `docs/awesome-iot-asp.md`, `docs/STUDY_PRIVATE.md`, `.claude/rules/docs-and-specs.md`,
  `CLAUDE.md` (invariants 7, 10).
