# M8 — Docs + E2E acceptance drain (#98 · #99 · #100)

Companion to the feature milestone note landed by the HomeNest / gemini-burst stack
([`M8-nest-gemini-soundburst-mvp.md`](M8-nest-gemini-soundburst-mvp.md) via PRs #114–#117).
This file indexes the **docs / offline acceptance** cells only — no OAuth client IDs,
no Device Access UUIDs, no live Nest console scraping.

## Docs / acceptance PRs

| Issue | PR | Spec / checklist |
|-------|-----|------------------|
| [#100](https://github.com/team-project-pikachu/IoT-ASP/issues/100) | [#125](https://github.com/team-project-pikachu/IoT-ASP/pull/125) | [`docs/specs/100-platform-matrix.md`](../specs/100-platform-matrix.md) · [`.vv/100/`](../../.vv/100/) |
| [#99](https://github.com/team-project-pikachu/IoT-ASP/issues/99) | [#126](https://github.com/team-project-pikachu/IoT-ASP/pull/126) | [`docs/glass-shatter-privacy.md`](../glass-shatter-privacy.md) · [`docs/specs/99-glass-shatter-privacy.md`](../specs/99-glass-shatter-privacy.md) |
| [#98](https://github.com/team-project-pikachu/IoT-ASP/issues/98) | [#127](https://github.com/team-project-pikachu/IoT-ASP/pull/127) | [`docs/specs/98-glass-shatter-e2e.md`](../specs/98-glass-shatter-e2e.md) · `tests/test_glass_shatter_e2e.py` |

## Feature stack (do not duplicate — extend docs/acceptance only)

| PR | Closes | Role |
|----|--------|------|
| [#114](https://github.com/team-project-pikachu/IoT-ASP/pull/114) | #96 | `AcousticEventClass` + `services/gemini-burst-detect` |
| [#115](https://github.com/team-project-pikachu/IoT-ASP/pull/115) | #101 | PWA `eventClass` / `glass_shatter` UI stub |
| [#116](https://github.com/team-project-pikachu/IoT-ASP/pull/116) | #102 | Swift Playground / `home-ios-build` SPM stub |
| [#117](https://github.com/team-project-pikachu/IoT-ASP/pull/117) | #97 | Glass Shatter Home wiring (stacks on #114) |

## Privacy split (no filename collision)

| Lane | Issue / PR | Public doc |
|------|------------|------------|
| Glass shatter Nest recording consent | #99 / #126 | `docs/glass-shatter-privacy.md` |
| SensorKit / CoreMotion / mic entitlements (M9) | #113 / #124 | `docs/privacy-entitlements-native.md` |

## Parked

- [#93](https://github.com/team-project-pikachu/IoT-ASP/issues/93) — live Nest OAuth (agents do not browser-login or invent client IDs).

## Offline verify

```bash
python3 -m pytest tests/test_glass_shatter_e2e.py tests/test_nest_events.py tests/test_nest_sdm.py -q
```
