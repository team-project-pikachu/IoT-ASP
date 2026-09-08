# SEBoK V&V matrix — Project 5 Todo wave

Living matrix. Evidence packages land under `.vv/<issue>/`. Do not mark Project Done without a fresh pass row.

**Scaffolded:** 2026-09-08 (Phase 1).  
**Guide:** [`docs/vv/README.md`](../docs/vv/README.md)

## Legend

| Column | Meaning |
|--------|---------|
| Req ID | Stable requirement identifier |
| Issue | GitHub issue owning the AC |
| Verify | Built-right procedure |
| Validate | Right-system procedure |
| Evidence | Path under `.vv/` |
| Status | `stub` → `in_progress` → `pass` / `fail` |

## Cross-cutting fleet invariants (C1–C6 + contract)

| Req ID | Statement | Issue(s) | Verify | Validate | Evidence | Status |
|--------|-----------|----------|--------|----------|----------|--------|
| C1-BT | Carrier TX = iOS native A2DP only; no Web Bluetooth TX | #12, #9 | Code/docs audit: no `navigator.bluetooth` for TX | Chrome iOS route uses system BT sink | `.vv/12/`, `.vv/9/` | stub |
| C3-SDD | App is SDD control surface (discover→…→execute) | #12 | UI + autoroute loop documented | Human Hold/Manual can override Gemini | `.vv/12/` | stub |
| C4-VOL | Default/max UI vol path 100%; clamps `vol_hard_max=100` | #12 | Unit: `validate_patch` accepts vol≤100; rejects >100 | Night curve not battery-duty; SPL still HW-limited | `.vv/12/` | stub |
| C5-120V | Continuous **120 V AC**; telemetry `power=ac120` | #12, #17 | Schema allows `power`; dry-run fixtures use `ac120` | No battery-save caps in autoroute prompts | `.vv/12/`, `.vv/17/` | stub |
| C6-LF | Default band 17–23 kHz; gated **10–20 Hz** when `lfDriveCapable` + armed | #12, #16 | Reject/skip LF when gate false; tag `band` | Systems check honesty when HW `na` | `.vv/12/`, `.vv/16/` | stub |
| SCH1 | Telemetry + patch `schemaVersion: 1` | #12, #17 | JSON schema / dry-run assert | Frontend polls only; no keys in HTML | `.vv/12/`, `.vv/17/` | stub |
| HOLD1 | Hold / Manual freezes remote patch apply | #12 | Flag in telemetry; worker respects hold | UI Hold blocks `/patch.json` apply | `.vv/12/` | stub |

## Issue #12 — Gemini continuous monitor + audio engineering

| Req ID | Statement | Verify | Validate | Evidence | Status |
|--------|-----------|--------|----------|----------|--------|
| I12-R1 | Ingest → clamp → Gemini/heuristic author → patch JSON | `bash scripts/autoroute_dev.sh` dry-run artifact | Hold blocks apply; production GET 200 | `.vv/12/` | stub |
| I12-R2 | Frontend telemetry beacon + `/patch.json` poll | Contract fields present | No Gemini keys in `public/index.html` | `.vv/12/` | stub |
| I12-R3 | Clamps enforce C4/C5/C6 | Clamp unit checks | Negative: out-of-band freq rejected | `.vv/12/` | stub |
| I12-N1 | Negative: bad patch rejected | `validate_patch` fails on illegal fields | — | `.vv/12/` | stub |

## Issue #16 — NS / seismo-acoustic priors

| Req ID | Statement | Verify | Validate | Evidence | Status |
|--------|-----------|--------|----------|----------|--------|
| I16-R1 | Physics priors documented with DOI/arXiv | `docs/physics.md` citations | Prior coeffs used in worker path | `.vv/16/` | stub |
| I16-R2 | Wire priors into autoroute prompt/tools + vib→algo | Code path includes prior weights | Synthetic vib fixtures change routing | `.vv/16/` | stub |
| I16-R3 | LF 10–20 Hz / `infra_felt` proxy when gated | Prior path respects C6 gate | Negative: nonsense prior ignored | `.vv/16/` | stub |

## Issue #17 — Colab + Gemini Enterprise pipeline

| Req ID | Statement | Verify | Validate | Evidence | Status |
|--------|-----------|--------|----------|----------|--------|
| I17-R1 | Notebook + pipeline doc: GCS → features → patch stubs | Offline dry cells; no secrets in git | Feature columns match telemetry contract | `.vv/17/` | stub |
| I17-R2 | SciPy anomaly (1 Hz / vib quantum) shared Colab/ADK module | Import/path documented | Aligns with SCH1 | `.vv/17/` | stub |
| I17-R3 | Credential refs only (1Password / env names) | Grep: no plaintext keys | — | `.vv/17/` | stub |

## Issue #9 — SensorKit + edge companions (research only)

| Req ID | Statement | Verify | Validate | Evidence | Status |
|--------|-----------|--------|----------|----------|--------|
| I9-R1 | Document Web cannot SensorKit; companions #14/#15/#18 | Research note completeness checklist | Chrome iOS sensor arm checklist | `.vv/9/` | stub |
| I9-R2 | No native Xcode entitlement work this wave | Diff excludes entitlement entitlements | Comment: implementation parked | `.vv/9/` | stub |

## Issue #13 — Multi-LLM registry (design sketch)

| Req ID | Statement | Verify | Validate | Evidence | Status |
|--------|-----------|--------|----------|----------|--------|
| I13-R1 | Registry interface + seat ladder (subscription-first) | Design doc review checklist | No production non-Gemini calls this wave | `.vv/13/` | stub |
| I13-R2 | Impl parked; future issue if needed | Design-only evidence | — | `.vv/13/` | stub |

## Backlog cross-links (not executed this wave)

| Issue | Note |
|-------|------|
| #14 | Pi5 USB-C |
| #15 | Apple Home / HomeKit / Matter |
| #18 | Node-3 infrasound HW |
| #19 | Notion hub |

## Known drift (blockers for later verify lanes)

| Drift ID | Detail | Affects |
|----------|--------|---------|
| DRIFT-VOL | `scripts/autoroute_dev.sh` asserts refuse for `vol=50` / hard max 20; `clamps.py` has `vol_hard_max=100` | I12-R1, C4-VOL |
| DRIFT-GCPDOC | Missing `docs/gcp-recordings.md` | ops / #17 evidence narrative |

## Revision

Phase 1: this matrix + `docs/vv/README.md` + stub dirs. Parallel exec lanes may fill `.vv/{12,16,17}/` with procedures/results; Status cells above stay `stub` until integrate lane promotes Project Done. Drift rows remain open until fixed.
