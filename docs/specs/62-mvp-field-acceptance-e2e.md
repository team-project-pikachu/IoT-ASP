# #62 — MVP field acceptance + Playwright e2e

## Status

Canonical checklist in `docs/field-acceptance-m0.md`; headless Playwright deepened for Soundcore / suddenFreq / nightNY presence; field lab owner-gated; **`e2e smoke` remains informative** (waiver until #63).

## Goal

Prove the three-phone Soundcore fleet path (A2DP, Signal on, incoherent hops, Hold/Manual, suddenFreq, night curve honesty, Soundcore roll-off) and document whether Playwright becomes a required check.

## Prior art

Reuse `tests/e2e/` + `docs/field-acceptance-m0.md` — do not add a second harness or Sonos path.

## Shipped (this shard)

| Artifact | Role |
|----------|------|
| `docs/field-acceptance-m0.md` | C1–C6 mapped FA checklist |
| `docs/issues/ISSUE-62-mvp-field-acceptance-e2e.md` | Issue stub + waiver |
| `tests/e2e/public_smoke.spec.mjs` | Extra M0 UI honesty assertions |
| `.vv/62/` | Evidence + blank FIELD-PASS template |
| `docs/ci.md` | Explicit informative waiver |

## Remaining scope

Owner field run (dated `FIELD-PASS.md`); optional CI promotion under **#63**.

## Wire fields

Fleet log keys per `RECORD_KEYS` / `docs/api-contract.md` (incl. `suddenFreq`, `nightNY`, `power=ac120`).

## Clamps / safety

C1 A2DP-only; Hold/Manual; no Web Bluetooth; C6 LF gated on Soundcore.

## Acceptance tests

- Checklist FA-01…FA-14 in `docs/field-acceptance-m0.md`
- `make e2e` / `bash tests/e2e/run.sh` exits 0

## CI gate

Informative `e2e smoke` job; required only after owner **#63** decision. Ruleset JSON unchanged by #62.

## Risks / HW limits

Soundcore DSP roll-off and night/local TZ skew are hardware/environment dependent; headless Chromium cannot close FA-01/FA-07/FA-11 hardware legs.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/62
- `docs/field-acceptance-m0.md`
- `docs/DESIGN_CONSTRAINTS.md`
- `docs/specs/01-m0-public-blaster.md`
