# Balanced build status — open issues

**Election:** 2 = Balanced (stub-first iterate).  
**Branch tip (this PR):** `feat/balanced-api-contract-vv` (stack PR7; base PR6 `feat/balanced-mvp-roadmap-docs`)  
**Date:** 2026-09-08

| Issue | Classification | Title | Key paths |
|------:|----------------|-------|-----------|
| #1 | implemented | M0 public Vercel hop blaster | `public/`, `vercel.json` |
| #2–#8, #10, #19, #24, #25 | parked stub | Design-only | `docs/specs/*` + `docs/issues/ISSUE-*` |
| #11 | static deepen | Fleet polish (non-React) | `public/index.html` (+ PR7 backend strip / stale) |
| #14/#15/#18/#39 | parked ADR+ | Edge / Beam | research docs |
| #22 | implemented+tests | Structured fleet logs | `fleet_log.py`, tests, demo script |
| #26 | fixture+dry-run+tests | Colab GCS features | fixtures + refuse LIVE_GCS |
| #27 | docs+name-check | Vercel Actions secrets | names-only; ORG/PROJECT set, TOKEN missing |
| #34 | implemented+tests | mdc_convert GEN_MARK | `scripts/mdc_convert.py` |
| #41 | stub+CLT check | Native iOS + watchOS | `native_compile_check.sh` |
| #42/#44/#45 | web slice | Impulse + alarm | `public/index.html` |
| #43 | docs | Soundcore specs | `docs/hardware/` |
| #46–#53 | closed dups | Pointers only | closed on GitHub |
| #60 | stub→dry-check | ADK Cloud Run deploy | PR8 dry-check script |
| #61 | qs+UI | Backend URL wiring | `?patch=` / `?telemetry=` + fleet strip |
| #62 | checklist+e2e | Field acceptance + e2e | checklist; e2e informative |
| #63 | applied+docs | Main protection | live ruleset active; status script in PR8 |
| #64 | in_progress soft | SEBoK V&V | `.vv/64/SOFTWARE-VERIFY.md` |
| #65 | closed tracker | closed-log automation | see #68 |
| #67 | parked/orthogonal | study vendor package | separate ADK vendor worktree |
| #68 | docs+workflow | Closed-issue log | `mvp-closed-log.md` + Action |
| #69 | docs | MVP roadmap | `mvp-roadmap.md` + README |

## Summary
- **Implemented / docs shipped:** #1 (already), #22 (extended), #26 dry-run (live pending), #27 docs, #34 GEN_MARK, #43 Soundcore docs.
- **Working stubs / web slices:** #11 static fleet cards, #41 native Xcode/SPM stub, #42/#44/#45 impulse+alarm web, #39 Sonos ADR + shell.
- **Parked ADR-only:** #2–#8, #10, #14, #15, #18, #19, #24, #25 (+ duplicates #46–#53). Do **not** unpark React rewrite (#10/#11 full), RLHF (#7/#8), or ADK 2.x (#24).
- **Blocked on owner secrets:** #27 (VERCEL_*), #26 live GCS (`GCP_SA_JSON` / `IOT_ASP_GCS_BUCKET` / `LIVE_GCS`).

## Overlap with open PRs
- PR #35 — same #34 GEN_MARK guard (landed here too for Balanced PR).
- PR #40 — Sonos #39 docs (this branch includes `docs/sonos-beam.md` + shell stub).
- PR #36 — ADK vendor (orthogonal; not forced here).
- **Implemented / docs shipped:** #1, #22 (+PR5 tests), #26 dry-run (+PR5 tests), #27 docs, #34, #41 CLT gate, #43.
- **Working stubs:** #11 static fleet, #42/#44/#45 impulse+alarm web, #39 Sonos ADR.
- **Parked ADR-only:** #2–#8, #10, #14, #15, #18, #19, #24, #25.
- **Duplicates #46–#53:** closed on GitHub; notes remain for pointers.
- **Blocked on owner secrets / HW:** #27, #26 live, #41 SensorKit, #60/#61 live URLs, Beam/Pi/HomeKit.
- **PR5:** tests + CLT native gate (#22/#26/#34/#41/#27 note).
- **PR6:** MVP roadmap/closed-log (#68/#69), #61 telemetry label, #60–#64 stubs, #62 checklist.
- **PR7:** api-contract pytest, fleet strip/stale, gyro wire fields, #64 software verify.
- **PR8:** #27 inventory (names), #63 live status script, #60 ADK dry-check.
- **Owner-gated:** #27 `VERCEL_TOKEN`, #26 live GCS, #41 SensorKit, #60/#61 live URLs, #64 `pass` rows, HW labs.

## Stacked PRs

See [STACKED-PRS.md](STACKED-PRS.md).
