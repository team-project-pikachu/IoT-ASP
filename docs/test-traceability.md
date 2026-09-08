# Test traceability — closed issues → automated tests

**Companion:** [TESTING_PLAN.md](TESTING_PLAN.md) · [architecture-pwa.md](architecture-pwa.md) · machine map: [`tests/fixtures/issue_test_map.json`](../tests/fixtures/issue_test_map.json)

**Epic tracker:** [#172 Platform: PWA test suite traceability](https://github.com/team-project-pikachu/IoT-ASP/issues/172)

## Method

1. Inventory closed issues (`gh issue list --state closed`).
2. Map each to pytest / Playwright / script seams that still enforce acceptance.
3. Prefer extending `tests/test_public_html.py` + `tests/e2e/public_smoke.spec.mjs`; add `tests/test_pwa_phase_*.py` per roadmap phase.
4. Duplicates (`aliasOf`) inherit the canonical issue’s tests.
5. Open issues stay in `openNextWave` until covered.

## Closed → test matrix (2026-09-08 inventory: **27** closed)

| # | Title (short) | Phase | Primary tests |
|---|---------------|-------|----------------|
| 1 | M0 public Vercel hop blaster | macos_pwa | `test_public_html` (literals/ids/HTML/README/no BT/keys); `test_pwa_phase_macos` (vercel.json, manifest); e2e load |
| 42 | Impulse→blast + alarm | macos_pwa | `test_impulse_alarm_and_fleet_stub`, `test_fleet_log_export_and_impulse_sim`; e2e fleet+simImpulse |
| 44–47, 50–51 | Dupes of #42 | macos_pwa | same as #42 |
| 12 | Gemini LLM autoroute design | platform_agentic | `test_agent_import`; Hold short-circuit; `autoroute_dev.sh` |
| 13 | Multi-LLM registry (parked) | platform_agentic | architecture doc present |
| 37 | Vercel webhooks | platform_agentic | `test_vercel_webhook*.py` |
| 17 | Colab + Gemini pipeline | platform_agentic | `test_colab_gcs_fixture.py` |
| 43 | Soundcore 2 specs | drivers | `test_soundcore_specs.py` |
| 49, 53 | Dupes of #43 | drivers | same |
| 34 | mdc_convert GEN_MARK | tooling | `test_mdc_convert.py` |
| 65 | mvp-closed-log append | tooling | `test_mvp_closed_log.py` |
| 67 | iot-asp-study vendor | tooling | `test_iot_asp_study.py` |
| 106 | Session worklog | tooling | closed-log + traceability doc |
| 9 | SensorKit research closeout | parked_docs | `test_native_compile_check.py` |
| 48, 52 | Dupes → open #41 | parked_docs | native compile check |
| 16, 19, 21, 23 | Research/docs parked | parked_docs | architecture / connectivity docs gates |
| 20 | Timestore SciPy | parked_docs | `test_features_live.py` |

**Mapped:** 27 / 27 closed issues have ≥1 test reference in `issue_test_map.json`.

## Phase modules

| Phase | Module | Milestone |
|-------|--------|-----------|
| macos_pwa | `tests/test_pwa_phase_macos.py` + `test_public_html.py` + e2e | macOS / Mac Studio |
| platform_agentic | existing agent/webhook/colab tests (+ future `test_pwa_phase_platform.py`) | Platform / Agentic / ADK |
| drivers | `test_soundcore_specs.py` | drivers + Sonos later |
| tooling | mdc / closed-log / study | Platform CI |

## Next open-issue wave (suggested)

| # | Why next |
|---|----------|
| 61 | Live telemetry/patch URL wiring (query overrides already gated) |
| 62 | Field checklist + expand Playwright |
| 3 | Continuous monitoring UAT alignment |
| 64 / 153 | SEBoK matrix → pass rows |
| 60 | ADK Cloud Run deploy path |

## Related

- [UAT.md](UAT.md) · [roadmap.md](roadmap.md) · [mvp-closed-log.md](mvp-closed-log.md)
