# SEBoK V&V — IoT-ASP Project 5 Todo wave

NASA SEBoK-style verification & validation for Project 5 **Todo** issues (#12, #16, #17, research #9, design #13).

**Testing plan:** [TESTING_PLAN.md](../TESTING_PLAN.md) · **UAT:** [UAT.md](../UAT.md) · **PRD:** [PRD.md](../PRD.md)

**Matrix:** [`.vv/matrix.md`](../../.vv/matrix.md)  
**Evidence roots:** `.vv/{9,12,13,16,17}/`  
**Constraints:** [DESIGN_CONSTRAINTS.md](../DESIGN_CONSTRAINTS.md) · [api-contract.md](../api-contract.md) · [power-fleet.md](../power-fleet.md)  
**Developer index:** [`.firecrawl/developer-index/INDEX.md`](../../.firecrawl/developer-index/INDEX.md)

## Lifecycle (per configuration item / issue)

1. **Requirements capture** — Req IDs from issue ACs + C1–C6 + `schemaVersion: 1`
2. **Verification** (built right) — schema, clamps, dry-run scripts, uniqueness/quantum self-checks, HTTP 200 when deploy lane runs
3. **Validation** (right system) — Chrome iOS arm path, Hold/Manual wins, native BT A2DP, no public PII, Gemini seats not called from every tab
4. **Evidence package** — under `.vv/<issue>/`: requirement IDs, procedure, observed result, revision hash, pass/fail
5. **Negative controls** — bad patch rejected; Hold blocks autoroute; out-of-band freq rejected; telemetry without secrets

**Promotion gate:** Project Status → Done only with fresh evidence for that issue.

## Fleet invariants (cross-cutting)

| ID | Invariant | Source |
|----|-----------|--------|
| C1 | Native Bluetooth A2DP only (no Web Bluetooth TX) | DESIGN_CONSTRAINTS |
| C2 | Pi USB-C field node (parked #14) | DESIGN_CONSTRAINTS |
| C3 | SDD via the app | DESIGN_CONSTRAINTS |
| C4 | Max practical Web Audio gain; `vol` UI 0–100 | DESIGN_CONSTRAINTS / clamps |
| C5 | Continuous **120 V AC** fleet power | power-fleet.md |
| C6 | Default 17–23 kHz; gated **10–20 Hz** when HW + user arm | DESIGN_CONSTRAINTS |
| SCH1 | Wire `schemaVersion: 1` | api-contract.md |
| HOLD1 | Hold / Manual freezes remote patch apply | api-contract.md |

## Issue → evidence dir

| Issue | Role | Evidence |
|-------|------|----------|
| [#12](https://github.com/team-project-pikachu/IoT-ASP/issues/12) | Gemini continuous monitor + autoroute | `.vv/12/` |
| [#16](https://github.com/team-project-pikachu/IoT-ASP/issues/16) | NS / seismo-acoustic priors | `.vv/16/` |
| [#17](https://github.com/team-project-pikachu/IoT-ASP/issues/17) | Colab + Gemini pipeline | `.vv/17/` |
| [#9](https://github.com/team-project-pikachu/IoT-ASP/issues/9) | SensorKit research only | `.vv/9/` |
| [#13](https://github.com/team-project-pikachu/IoT-ASP/issues/13) | Multi-LLM registry design sketch | `.vv/13/` |

Backlog cross-links only (not this wave): #14 Pi5, #15 Apple Home, #18 node-3 infrasound, #19 Notion hub.

## Known drift (later lanes — Phase 1 notes only)

- `scripts/autoroute_dev.sh` still asserts old vol refuse (`vol=50` must fail / hard max 20) while `services/autoroute-adk/iot_asp_autoroute/clamps.py` sets `vol_hard_max=100` (C4).
- Missing `docs/gcp-recordings.md` for GCP `bear-iot-asp-rec`.

## Phase status

- Phase 1: matrix + stubs + developer-index (this document).
- Later: exec lanes fill `.vv/<n>/EVIDENCE.md` with procedures and results.
