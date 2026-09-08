# #69 — MVP feature roadmap document

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/69 · Labels: `docs` · Related: [#68](68-mvp-closed-log.md), `docs/specs/README.md`
## Status
**Implemented in this PR.** Canonical milestone → issue map lives at `docs/mvp-roadmap.md`.
## Goal
One public roadmap that maps M0–M5 (and supporting MVP / post-MVP lanes) to Project 5 issues and specs so implementers know the web-ship close order without reading every issue body.
## Prior art
| What | Where | Decision |
|------|-------|----------|
| Spec index | `docs/specs/README.md` | Roadmap links specs; does not fork wire tables |
| Balanced stub board | `docs/issues/BALANCED-BUILD-STATUS.md` | May lag; roadmap is canonical |
| Closed-log (#68) | `docs/mvp-closed-log.md` | Audit trail for closed issues |
## Shipped
| What | Where |
|------|-------|
| Milestone / issue / spec map + close order | `docs/mvp-roadmap.md` |
| `#60` clarified as MVP deploy gate despite M6 milestone | same file § Post-MVP note + Supporting MVP row |
| Spec index rows for #68 / #69 | `docs/specs/README.md` |
## Remaining scope
- Refresh open-issue snapshot via `gh` when milestones change (manual).
# #69 — Durable MVP feature roadmap
`docs/mvp-roadmap.md` maps milestones M0–ship to issue numbers; living doc with closed-log convention.
Keep a durable milestone → issue map for the web MVP ship path without relying on Project board UI alone.
Pair with `docs/mvp-closed-log.md` (#65/#68) and `docs/specs/README.md`; do not duplicate closed chronology in the roadmap table.
## Shipped on `main`
In-flight with Balanced PR6 / related docs PRs.
Update milestone rows only when ownership changes; closes go to the closed log.

## Wire fields

None.

## Clamps / safety

- No site PII; no secret values.
- Do not claim HW capabilities beyond `docs/DESIGN_CONSTRAINTS.md` (C1/C2).

## Acceptance tests
1. `docs/mvp-roadmap.md` exists and links `#68` / `#69` / `#60`.
2. Close order lists `#60` before field/e2e ship gates.
3. Post-MVP section notes `#60` remains an MVP gate.
4. Spec files `68-mvp-closed-log.md` and `69-mvp-roadmap.md` are indexed in `docs/specs/README.md`.
## CI gate
None beyond docs presence checks covered by closed-log / study package tests referencing the roadmap path.
## Risks / HW limits
- Board / milestone drift; treat GitHub Project 5 as live status and this file as the intended map.
## Sources
- GitHub issue #69; Project 5 board; `docs/specs/README.md`.
Public docs stay generic (no street addresses / PII).
Roadmap links resolve; closed-log convention documents timeline-comment + `--backfill`.
Doc presence asserted by `tests/test_mvp_closed_log.py`.
Stale milestone rows if not updated when issues move.
- https://github.com/team-project-pikachu/IoT-ASP/issues/69
- `docs/mvp-roadmap.md`
