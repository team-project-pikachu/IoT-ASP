# Burst → shriek / extreme variance (evidence)

**Config item:** `services/autoroute-adk/iot_asp_autoroute/mic_diff.py` + `tests/test_mic_diff.py`
**Spec:** `docs/specs/25-hw-limited-lf-aec-micdiff.md`
**Branch:** `claude/mdc-conversion-features-gu3yzk` (base `4e4f5db`)
**Date:** 2026-09-08 (UTC) — refreshed after the adversarial-review fix round (same day)
**Environment:** Python 3.11.15, numpy 2.4.6 (CI: 3.12 + `requirements-dev.txt`)
**SEBoK plan:** not modified · **Secrets:** none read or printed · **Site PII:** none

## Detection rule

| ID | Requirement |
|----|-------------|
| BS-01 | `MIC_DIFF_ALPHA == 0.85`; `mic_diff(mic, out, alpha)` = `mic − alpha·out`, passthrough when `outLevel` missing |
| BS-02 | `calibrate_alpha` = least squares through origin (`numpy.linalg.lstsq`), clamp `[0, 2]`, refuse `< 3` pairs / no variance |
| BS-03 | `aec_capability` → `fullAEC False`, `path output-bus-subtraction`, for every user agent |
| BS-04 | `lf_capability` → `lfMic False` always; `lfTx == priors.lf_drive_capable(t)` |
| BS-05 | `burst_decision` monotone in `thr_db` (strict `>`); `hold_manual=True` refuses for every `micDiff` |
| BS-06 | `apply_burst_bias` → `shriek_chirp`, `shriekMs + 15` clamped to `[20, 120]`; `validate_patch` still passes |
| BS-07 | `hw_limits_report` → four limits `full_aec`, `lf_mic`, `lf_tx`, `alpha_calibration`, docs + `#9` pointers, no URLs |
| BS-08 | CLI `python3 -m iot_asp_autoroute.mic_diff --demo` exits 0, deterministic; no args → exit 2 |
| BS-09 | Module imports without scipy / google; source has no CFD / Navier / Web Bluetooth claims |
| BS-10 | `apply_burst_bias` **refuses, never rewrites**: a base patch `clamps.validate_patch` refuses (`shriekMs` 500 / −100 / 0 / `"abc"`, `algo` off-whitelist, `fMin ≥ fMax`, `pulseMs`/`vol` out of range) comes back as an untouched copy and `validate_patch` still refuses it with the same message (`burst_bias_eligibility`) |
| BS-11 | Spec `docs/specs/25-…md` carries the eleven mandatory sections in order incl. **Prior art** (`.claude/rules/docs-and-specs.md`) |

   `micDiff_band = micEnergy_band − α · outLevel_band` (α = `OUT_ALPHA` ≈ 0.85)

   If `outLevel &lt; −90 dB` (TX silent), `micDiff_band = micEnergy_band`.

4. `micDiff = max(micDiff_lf, micDiff_us)` (0.1 dB quantize).
5. Rolling EMA baseline of `micDiff`. Onset when `micDiff − baseline &gt; BURST_ONSET_DB` (~9 dB).
6. `bandBurst` = `lf` \| `us` \| `both`.

## Response algorithm

1. **Hold/Manual** → refuse / `exitExtremeMode`.
2. On onset (and while `micDiff` stays above release hysteresis): set `soundBurst=true`, `extremeActive=true`.
3. Every `BURST_JITTER_MS` (~450 ms): pick `shriek_chirp` \| `shriek_sweep` \| `burst`; jitter dwell / `shriekMs` / vol (0.5-step, night ≤ `nightTargetVol`) / optional seed jump — all clamped.
4. Align TX: default **17–23 kHz**; if `bandBurst` ∈ {`lf`,`both`} and `lfDriveCapable` → optional **10–20 Hz**.
5. Exit after **`BURST_QUIET_MS` (~2.5 s)** with `micDiff` settled below release threshold → resume normal autoroute.

## Telemetry (schemaVersion 1)

`soundBurst`, `extremeActive`, `bandBurst`, `micEnergy`, `outLevel`, `micDiff` / `micNet`, `soundBurstMeta.{energyDelta,baselineDb,onsetDb,micDiffLf,micDiffUs,outAlpha}`.

## Backend

`priors.sound_burst` + `SOUND_BURST_ALGO_BIAS`; `author_sudden_freq_patch` shriek-weights when `soundBurst`/`extremeActive`.

## Honesty / HW limits

- Full acoustic echo cancellation not available in Safari/Chrome iOS Web Audio for this path.
- LF mic bins limited by FFT resolution / mic HPF; LF TX gated by `lfDriveCapable` (Soundcore/A2DP typically **na**).
- Project 5 issue for residual HW-limited sensing/TX.

## Verify

```bash
bash scripts/autoroute_dev.sh
node --check <(sed -n '/<script>/,/<\/script>/p' public/index.html | sed '1d;$d')  # or extract JS
```

Docs: [algorithms.md](../docs/algorithms.md) § Environmental sound burst.

| Command | Exit | Result |
|---------|------|--------|
| `python3 -m pytest tests/test_mic_diff.py -q` | 0 | `21 passed` (MD-01 … MD-19; MD-18 = refuse-never-rewrite regression, MD-19 = spec sections / Prior art) |
| `python3 -m iot_asp_autoroute.mic_diff --demo` | 0 | JSON below; two consecutive runs byte-identical |
| `python3 -m iot_asp_autoroute.mic_diff` | 2 | `usage: python3 -m iot_asp_autoroute.mic_diff [-h] [--demo]` on stderr, empty stdout |
| `bash scripts/ci_static_gates.sh` | 0 | `OK ci_static_gates` |
| `bash scripts/autoroute_dev.sh` | 0 | `DRY-RUN OK` / `OK fleet_log jsonl` (burst hook is on the dry-run path via `sudden_freq.py:133-135`; dry-run telemetry has no burst keys → no bias → unchanged output) |
| `python3 -m pytest tests -q` | 0 | `213 passed` (whole suite, fix round; earlier baseline `51 passed` before the other work items landed) |

## Deploy

| Field | Value |
|-------|--------|
| **Prod alias** | https://hop-ultrasonic.vercel.app/ |
| **Immutable** | https://hop-ultrasonic-1v9i9gmot-1digital-design.vercel.app |
| **Inspect** | https://vercel.com/1digital-design/hop-ultrasonic/HQvRWp1PjkeTcafQJpXpkd6TQU2e |
| **Project 5 HW issue** | https://github.com/team-project-pikachu/IoT-ASP/issues/25 |
| **Sim** | `autoroute_dev.sh` DRY-RUN OK; burst author `trigger=soundBurst`; Hold refuse OK; `node --check` OK |

## Backend HW-limit verification (#25)

The frontend path is paired with
`services/autoroute-adk/iot_asp_autoroute/mic_diff.py`. It uses
`MIC_DIFF_ALPHA == 0.85`, passes through mic energy when `outLevel` is
absent, calibrates alpha by least squares through the origin (clamped
to `[0, 2]`), and refuses burst decisions while Hold / Manual is active.
`apply_burst_bias` selects `shriek_chirp`, clamps `shriekMs` to
`[20, 120]`, and passes the authoritative patch validator. Capability
reporting explicitly distinguishes output-bus subtraction from full
AEC and keeps LF mic/TX hardware limitations visible.

```bash
python3 -m pytest tests/test_mic_diff.py tests/test_public_html.py -q
PYTHONPATH=services/autoroute-adk python3 -m iot_asp_autoroute.mic_diff --demo
```

## HW-limited leftovers (issue #25) — pass/fail

| Limit | Status | Evidence |
|-------|--------|----------|
| `full_aec` — full AEC on iOS Safari / Chrome Web Audio | **limited** (by design, honest) | `aec_capability()["fullAEC"] is False` for `None`, `""`, iOS Safari, iOS Chrome, desktop UAs (MD-12); shipped path = output-bus subtraction α = 0.85 |
| `lf_mic` — <20 Hz mic capture | **limited** (by design, honest) | `lf_capability()["lfMic"] is False` for all 7 fixtures (MD-13); 23.44 Hz/bin argument on the wire; `lfEnergy` documented as accelerometer felt proxy |
| `lf_tx` — LF 10–20 Hz TX over A2DP | **gated** | `lfTx == priors.lf_drive_capable(t)`; `True` only with `lfDriveCapable: True` or `lfArmed` + LF band; `False` under `holdManual` (MD-13, MD-17) |
| `alpha_calibration` — α per device / BT route | **calibrated in demo** | seed-25 fit recovers `0.8575` (|Δ| < 0.1); exact-fit pairs → `0.85 ± 1e-9`; slope 10 → clamped `2.0`; slope −3 → clamped `0.0`; `< 3` pairs / zero `outLevel` → `ok False`, default `0.85` (MD-04 … MD-06) |

## Safety invariants exercised

| Invariant | Test |
|-----------|------|
| Hold / Manual wins (refuse for `micDiff ∈ {None, −10, 0, 6.01, 40, 1e9}`; flags ignored under hold) | MD-09 |
| `shriekMs` clamp `[20, 120]` — `110 + 15 → 120.0`, never `125`; bogus bias 999 ignored | MD-11, MD-17 |
| Refuse, never silently rewrite (invariant 5) — out-of-policy base (`shriekMs` 500 → stays 500, `validate_patch` → `shriekMs=500.0 outside [20.0,120.0]`; `0` / `"abc"` / `algo evil` / `fMin ≥ fMax` likewise); only the +15 delta is clamped (`20 → 35`, `105 → 120`); through `author_sudden_freq_patch`: `micDiff 9` → `shriek_chirp`, `shriekMs 70.0`, `burstBias`; hold → refused upstream | MD-18 |
| Spec section order incl. Prior art (five venues, `docs/PRIOR_ART.md`, `features_live.py` cited) | MD-19 |
| `algo` whitelist — `BURST_ALGO in ALLOWED_ALGOS`; `validate_patch(out)[0] is True` | MD-01, MD-11 |
| `vol_hard_max == vol_soft_max == 100.0`; `apply_burst_bias` never touches `vol`/`fMin`/`fMax`/`band` | MD-01, MD-11 |
| No CFD / Navier / Web Bluetooth strings; no `os.environ`; fresh import adds no `scipy` / `google` modules | MD-15 |
| Deterministic CLI (seeded, no timestamps) | MD-16 |

## Integration (integrator-owned files — landed on the branch, verified by reading)

- `sudden_freq.py:9`, `:133-135` — `burst_decision_from_telemetry` + `apply_burst_bias` after the duty bias, before `validate_patch` (holdManual refuse at `:67-68` runs first).
- `tools.py:13`, `:236-244` — tool `hw_limits_report()`; `agent.py:20`, `:67` registration; `.github/workflows/ci.yml:81-85` import smoke.
- `docs/api-contract.md` — additive patch row `burstBias` present.

## Fix round (adversarial review, 2026-09-08)

| Finding | Root cause | Fix | Regression |
|---------|-----------|-----|------------|
| `apply_burst_bias` laundered an out-of-policy `shriekMs` (500 → 120, −100 → 20, 0 / `"abc"` → 65) into an accepted patch | Helper clamped the **input** instead of refusing it; had its own copy of the policy | `burst_bias_eligibility` runs `clamps.validate_patch` (single source of truth) first; ineligible drafts return untouched so the downstream `validate_patch` refuses them with its own message; only the +15 delta is clamped | MD-18 (8 refusable bases + boundaries + end-to-end through `author_sudden_freq_patch`) |
| Spec lacked the mandatory `## Prior art` section | Section omitted when the spec was authored | Added *Prior art* (repo / Mac clone / org repos / awesome-lists / Context7 + Firecrawl, build-vs-adopt decision with sources) | MD-19 (heading order + venue names + citations) |

Demo JSON after the fix: byte-identical to the table above (`micDiff 5.5`, `calibration.alpha 0.8575`, `burst.extreme true` at 13.5 dB, `burstHold.reason "holdManual — refuse"`, `aec.fullAEC false`, `lf.lfMic false`, 4 limits); two consecutive runs `cmp` identical; no-arg run exit 2.
