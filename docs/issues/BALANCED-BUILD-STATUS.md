# Balanced build status — open issues

**Election:** 2 = Balanced (stub-first iterate).
**Branch tip:** `feat/balanced-test-native-ci` (stack PR5; base PR4 `feat/balanced-native-hw-research`)
**Date:** 2026-09-08

| Issue | Classification | Title | Key paths |
|------:|----------------|-------|-----------|
| #1 | implemented | M0 public Vercel hop blaster | `public/`, `vercel.json`, `docs/specs/01-m0-public-blaster.md` |
| #2 | parked stub | Max-entropy seeds | `docs/specs/02-max-entropy-seeds.md` + `docs/issues/ISSUE-02-*` |
| #3 | parked stub | Continuous polling & monitoring | `docs/specs/03-continuous-monitoring-watchdog.md` + `docs/issues/ISSUE-03-*` |
| #4 | parked stub | Physical vib (DeviceMotion) | `docs/specs/04-06-vibration-channels.md` + `docs/issues/ISSUE-04-*` |
| #5 | parked stub | Acoustic vib (mic energy) | `docs/specs/04-06-vibration-channels.md` + `docs/issues/ISSUE-05-*` |
| #6 | parked stub | Material-dependent channel selection | `docs/specs/04-06-vibration-channels.md` + `docs/issues/ISSUE-06-*` |
| #7 | parked stub | RLHF positive loop | `docs/specs/07-08-rlhf-loops.md` + `docs/issues/ISSUE-07-*` |
| #8 | parked stub | RLHF negative loop | `docs/specs/07-08-rlhf-loops.md` + `docs/issues/ISSUE-08-*` |
| #10 | parked stub | React / React Strict DOM rewrite | `docs/specs/10-11-react-rewrite.md` + `docs/issues/ISSUE-10-*` |
| #11 | static deepen | React multi-device fleet polish | `docs/specs/10-11-react-rewrite.md` + `docs/issues/ISSUE-11-*` |
| #14 | parked ADR+ | Raspberry Pi 5 field node | `docs/specs/14-15-21-23-edge-integrations.md` + `docs/issues/ISSUE-14-*` |
| #15 | parked ADR+ | Apple Home / HomeKit / Matter | `docs/specs/14-15-21-23-edge-integrations.md` + `docs/issues/ISSUE-15-*` |
| #18 | parked ADR+ | Node-3 chair + infrasound proxy | `docs/specs/18-node3-chair-infrasound.md` + `docs/issues/ISSUE-18-*` |
| #19 | parked stub | Notion hub | `docs/specs/19-notion-hub.md` + `docs/issues/ISSUE-19-*` |
| #22 | implemented+tests | Structured fleet logs | `fleet_log.py`, `tests/test_fleet_log.py`, `scripts/fleet_log_demo.sh` |
| #24 | parked stub | google-adk / google-genai 2.x | `docs/specs/24-adk-2x-migration.md` + `docs/issues/ISSUE-24-*` |
| #25 | parked stub | HW-limited LF/AEC micDiff | `docs/specs/25-hw-limited-lf-aec-micdiff.md` + `docs/issues/ISSUE-25-*` |
| #26 | fixture+dry-run+tests | Colab live GCS features | `features_live.py`, `colab_gcs_fixture.sh`, `colab_etl_dry_run.py`, fixtures |
| #27 | docs+name-check | Vercel Actions secrets | `docs/deploy.md`, `vercel_secrets_check.sh` (+ Development item title note) |
| #34 | implemented+tests | mdc_convert GEN_MARK guard | `scripts/mdc_convert.py`, `tests/test_mdc_convert.py` |
| #39 | parked research+ | Sonos Beam Gen 2 sink | `docs/sonos-beam.md` + `docs/issues/ISSUE-39-*` |
| #41 | stub+CLT check | Native iOS + watchOS | `native/IoTASP/`, `scripts/native_compile_check.sh`, `make native-check` |
| #42 | web slice | Impulse→blast + alarm (combined) | `public/index.html`, `docs/algorithms.md` |
| #43 | docs+native align | Soundcore manufacturer specs | `docs/hardware/soundcore-specs.md` |
| #44 | web slice (canon) | Web PWA impulse→blast | merged intent → #42; dups #46/#50 closed |
| #45 | web slice (canon) | Web PWA alarm reactivity | merged intent → #42; dups #47/#51 closed |
| #46–#53 | closed dups | Point to #41/#42/#43/#44/#45 | `docs/issues/ISSUE-4{6-9}-*` / `ISSUE-5{0-3}-*` |
| #60 | stub | ADK Cloud Run / Agent Engine | `docs/issues/ISSUE-60-*` (PR6) |
| #61 | stub+qs | Wire live backend URLs | query `?patch=` / `?telemetry=` already; live URLs owner-gated |
| #62 | stub | Field acceptance + e2e promote | `tests/e2e/` + checklist (PR6) |
| #63 | stub | Main branch protection ruleset | `docs/branch-protection.md` |
| #64 | stub | SEBoK V&V MVP pass matrix | `.vv/matrix.md` |
| #68 | docs | Closed-issue logging | `docs/mvp-closed-log.md` (PR6) |
| #69 | docs | MVP feature roadmap | `docs/mvp-roadmap.md` (PR6) |

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

## Stacked PRs

See [STACKED-PRS.md](STACKED-PRS.md).
