# RED team PASS — IoT-ASP partial greens (adversarial audit)

| Field | Value |
|-------|--------|
| **Audit UTC** | `2026-09-08T00:13:22Z` |
| **Revision** | `e41c3c0e76ef9e0d9ddb59995cc7faf769a8bb79` (`e41c3c0`) |
| **Plan** | `~/.cursor/plans/iot-asp_sebok_e2e_a0905e55.plan.md` |
| **Repo** | `/Users/machine/apps/IoT-ASP` |
| **Note** | Partial / conditional greens only. Overall promotion gate: **FAIL** — see [FAIL.md](FAIL.md). |

---

## P1 — No Gemini/Vertex secrets in public HTML

| File:line | Evidence |
|-----------|----------|
| `public/index.html:395` | Copy states browser never embeds Gemini keys |
| `public/index.html:456–465` | Backend constants are URLs/paths only; empty strings — no `AIza*`, `sk-*`, Bearer tokens, or Vertex client |
| Grep over `public/` | No API key material in HTML/JS |

**api-contract invariant 1** satisfied for secret embedding (URL wiring still empty — see FAIL F3).

---

## P2 — C4 / C5 clamp constants match design docs (backend)

| File:line | Evidence |
|-----------|----------|
| `docs/DESIGN_CONSTRAINTS.md:31–47` | C4 max Web Audio 100%; C5 continuous 120 V AC |
| `services/autoroute-adk/iot_asp_autoroute/clamps.py:15–21` | Soft==hard **100**; comment documents C5 (no battery vol caps) |
| `public/index.html:553` | `VOL_PATCH_MAX = 100` (intent; moot until FAIL F1 fixed) |
| `public/index.html:575` | `POWER_FLEET = "ac120"` |

---

## P3 — Dual band limits implemented in backend clamps (C6)

| File:line | Evidence |
|-----------|----------|
| `clamps.py:11–13,30–44` | `BAND_US` 17–23 kHz; `BAND_LF` 10–20 Hz; `band_limits()` from tag / inferred `fMin` |
| `clamps.py:67–74` | Out-of-band `fMin`/`fMax` refused |

---

## P4 — C1 messaging: no Web Bluetooth TX path in code

| File:line | Evidence |
|-----------|----------|
| `public/index.html:13,239,365,400,1835–1836` | Explicit “not Web Bluetooth”; Systems check row for native A2DP |
| Grep | No `navigator.bluetooth` / Web Bluetooth API usage |

---

## P5 — Author path Hold refuse (when telemetry flag set)

| File:line | Evidence |
|-----------|----------|
| `sudden_freq.py:33–34` | `holdManual` → `is_sudden_freq_event` false |
| `sudden_freq.py:67–68` | `author_sudden_freq_patch` returns `(False, "holdManual — refuse patch", {})` |

Observed under audit: author refuses Hold telemetry. (Does **not** cover `write_patch` bypass — FAIL F7.)

---

## P6 — Happy-path offline dry-run produces patch artifact

| Procedure | Result |
|-----------|--------|
| `bash scripts/autoroute_dev.sh` | Exit **0**; `DRY-RUN OK` |
| Artifact | `.autoroute-dry/meta/patches/node1.json` with `schemaVersion: 1`, `vol: 100.0`, wire algo, `priors` labels |
| Module | `python3 -m iot_asp_autoroute.dry_run` |

Satisfies **smoke** verification only — not negative controls (FAIL F2).

---

## P7 — SciPy vib anomaly dry-run module present

| File:line | Evidence |
|-----------|----------|
| `vib_anomaly.py` + `dry_run_anomaly.py` | Offline synthetic 1 Hz series; SciPy medfilt / MAD / peaks |
| Run | `python3 -m iot_asp_autoroute.dry_run_anomaly` → JSON `ok` with anomaly flags |

Useful for #17 SciPy path docs; not wired into Colab `.ipynb` (FAIL F5).

---

## P8 — Contract / constraint docs exist and cite C1–C6

| File | Evidence |
|------|----------|
| `docs/DESIGN_CONSTRAINTS.md` | Formal C1–C6 tables |
| `docs/api-contract.md` | `schemaVersion: 1`, telemetry + patch schemas, Hold narrative, C5/C6 |
| `docs/physics.md` + `reference/LITERATURE.md` | Prior art / DOI lineage for #16 docs track |
| `services/autoroute-adk/.env.example` | Credential **names** only |

---

## P9 — Production static host responds

| Check | Result |
|-------|--------|
| `curl -sS -o /dev/null -w '%{http_code}' https://hop-ultrasonic.vercel.app/` | **200** |

Confirms deploy liveness of static surface; **not** live ADK/ingest loop (FAIL F3).

---

## P10 — Ingest / tools accept contract aliases

| File:line | Evidence |
|-----------|----------|
| `tools.py:114–118` | `absA`/`a`, `audioContextState`/`ctxState` normalization |

---

## What these PASSes do **not** authorize

- Project Status → Done for #12 / #16 / #17  
- Claims that Hold works in Chrome iOS (FAIL F1)  
- Claims that dry-run proves clamp refusal for over-max vol (FAIL F2)  
- Claims that NS/seismo priors are scored/weighted in the worker (FAIL F4)  
- Claims that Colab ETL notebook is runnable e2e (FAIL F5)

Re-read FAIL.md after any green fixes; write a new timestamped audit pair under `.vv/red/` (or dated subdirectory) before promotion.
