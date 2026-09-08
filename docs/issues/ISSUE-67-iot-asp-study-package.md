# ISSUE-67 — Vendor IoT-ASP-study as public-safe packages/iot-asp-study

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/67  
**Classification:** ship / iterate (Balanced) — post-MVP / research, not M0–M5 blaster MVP  
**Status:** package vendored; private protocol not copied

## Did

- `packages/iot-asp-study/` — importable public-safe scaffold (schema, path resolver, scrub heuristics, doctor, placeholder templates). Provenance: vendored scaffold, **not** git subtree / submodule of private `IoT-ASP-study`.
- `tests/test_iot_asp_study.py` — sidecar validation + fail-closed PII markers on public templates.
- Pointers only: `docs/STUDY_PRIVATE.md`, `README.md`, `CLAUDE.md` (gitignored `study/` unchanged).
- Companion URL documented in `packages/iot-asp-study/PROVENANCE.md`.

## Didn't

- Dump site protocol, street addresses, neighbor identifiers, recording bucket URIs, seat emails, or raw audio.
- `git subtree` / submodule the private companion onto public `main`.
- Rewrite ADK / Vercel, bump `schemaVersion`, change vol clamps or Hold / Manual.
- Copy stacked #68/#69 files (`docs/mvp-roadmap.md`, `docs/mvp-closed-log.md`, closed-log workflow/script, ISSUE-60..69 stubs).

## Next

- Operators clone `team-project-pikachu/IoT-ASP-study` (or keep local gitignored `study/`) and set `IOT_ASP_STUDY_ROOT` when they need private protocol.
- Optional later: map a post-MVP row in the canonical roadmap doc when that file exists on `main` (#69).
- Human verifies this PR; do not auto-close without review.
