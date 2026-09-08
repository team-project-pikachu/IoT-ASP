# Balanced build status — open issues

**Election:** 2 = Balanced (stub-first iterate).
**Branch tip (this PR):** `feat/m8-nest-gemini-home-ios` (stack on PR8 `feat/balanced-ops-secrets-adk`)
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
| #11 | parked stub | React multi-device fleet polish | `docs/specs/10-11-react-rewrite.md` + `docs/issues/ISSUE-11-*` |
| #14 | parked stub | Raspberry Pi 5 field node | `docs/specs/14-15-21-23-edge-integrations.md` + `docs/issues/ISSUE-14-*` |
| #15 | parked stub | Apple Home / HomeKit / Matter | `docs/specs/14-15-21-23-edge-integrations.md` + `docs/issues/ISSUE-15-*` |
| #18 | parked stub | Node-3 chair + infrasound proxy | `docs/specs/18-node3-chair-infrasound.md` + `docs/issues/ISSUE-18-*` |
| #19 | parked stub | Notion hub | `docs/specs/19-notion-hub.md` + `docs/issues/ISSUE-19-*` |
| #22 | implemented | Structured fleet logs | `services/autoroute-adk/iot_asp_autoroute/fleet_log.py`, `tests/test_fleet_log.py`, `docs/specs/22-structured-fleet-logs.md` |
| #24 | parked stub | google-adk / google-genai 2.x | `docs/specs/24-adk-2x-migration.md` + `docs/issues/ISSUE-24-*` |
| #25 | parked stub | HW-limited LF/AEC micDiff | `docs/specs/25-hw-limited-lf-aec-micdiff.md` + `docs/issues/ISSUE-25-*` |
| #26 | stubbed-live | Colab live GCS features | `services/autoroute-adk/iot_asp_autoroute/features_live.py`, `notebooks/iot_asp_colab_etl.md`, `scripts/colab_live_gcs.sh` |
| #27 | docs+inventory | Vercel Actions secrets | ORG/PROJECT set; **TOKEN missing**; `gh_secrets_names_check.sh` |
| #34 | implemented | mdc_convert GEN_MARK guard | `scripts/mdc_convert.py`, `tests/test_mdc_convert.py`, `docs/mdc-conversion.md` |
| #39 | parked stub | Sonos Beam Gen 2 sink | `docs/specs/39-sonos-beam-sink.md` + `docs/issues/ISSUE-39-*` |
| #41 | stubbed | Native iOS + watchOS | `docs/specs/41-native-ios-watchos.md`, `native/IoTASP/`, `.vv/41/README.md` |
| #42 | stubbed | Impulse→blast + alarm (combined) | `docs/specs/42-impulse-alarm-combined.md`, `public/index.html`, `.vv/42/README.md` |
| #43 | implemented-docs | Soundcore manufacturer specs | `docs/specs/43-soundcore-manufacturer-specs.md`, `docs/hardware/soundcore-specs.md` |
| #44 | stubbed | Web PWA impulse→blast | `docs/specs/44-web-pwa-impulse-blast.md`, `public/index.html`, `.vv/42/README.md` |
| #45 | stubbed | Web PWA alarm reactivity | `docs/specs/45-web-pwa-alarm-reactivity.md`, `public/index.html`, `.vv/42/README.md` |
| #46 | duplicate | dup of #44 | see #44 |
| #47 | duplicate | dup of #45 | see #45 |
| #48 | duplicate | dup of #41 | see #41 |
| #49 | duplicate | dup of #43 | see #43 |
| #50 | duplicate | dup of #44 | see #44 |
| #51 | duplicate | dup of #45 | see #45 |
| #52 | duplicate | dup of #41 | see #41 |
| #53 | duplicate | dup of #43 | see #43 |
| #60 | dry-check | ADK Cloud Run deploy | `scripts/adk_deploy_dry_check.sh` (no live deploy) |
| #63 | status script | Main protection apply | `scripts/gh_protect_main_status.sh` (report-only) |

## Summary
- **Implemented / docs shipped:** #1 (already), #22 (extended), #26 dry-run (live pending), #27 docs+inventory, #34 GEN_MARK, #43 Soundcore docs.
- **Working stubs:** #11 static fleet cards, #41 native Xcode/SPM stub, #42/#44/#45 impulse+alarm web, #39 Sonos ADR + shell.
- **M8 (this PR):** Nest cameras + Gemini sound-burst + glass shatter; `make home-ios-build` stub; #15 cross-linked (Apple ≠ Google).
- **PR8 (stack base):** #27 Actions inventory (ORG/PROJECT yes, TOKEN no), #63 ruleset status script, #60 ADK layout dry-check.
- **Parked ADR-only:** #2–#8, #10, #14, #15, #18, #19, #24, #25 (+ duplicates #46–#53).
- **Blocked on owner secrets:** #27 (`VERCEL_TOKEN`), #26 live GCS (`GCP_SA_JSON` / `IOT_ASP_GCS_BUCKET` / `LIVE_GCS`).

## Overlap with open PRs
- PR #35 — same #34 GEN_MARK guard (landed here too for Balanced PR).
- PR #40 — Sonos #39 docs (this branch includes `docs/sonos-beam.md` + shell stub).
- PR #36 — ADK vendor (orthogonal; not forced here).
- PR #73 — MVP roadmap/closed-log stubs for #60–#69 (coordinate on merge).

## Stacked PRs

See [STACKED-PRS.md](STACKED-PRS.md).

## Outstanding themes (log-only — 2026-09-08)

1. **Merge order / conflicts:** resolve `#70` and `#76` before tip `#105`.
2. **Secrets:** Vercel `#27`, GCS `#26`, Nest/OAuth `#83`/`#93`.
3. **Nest console / Gemini live:** M8 `#87`/`#103` stubbed only.
4. **HW parked:** `#104`/`#39`/`#14`/`#18`.
5. **Field + V&V:** `#61`→`#62`→`#64`.

Comments + project 5 board refreshed same day; see [STACKED-PRS.md](STACKED-PRS.md).
