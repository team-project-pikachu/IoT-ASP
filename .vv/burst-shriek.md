# Burst → shriek / extreme variance (evidence)

| Field | Value |
|-------|--------|
| **UTC** | `2026-09-08T00:37:52Z` |
| **Repo** | `IoT-ASP` → sync `hop-ultrasonic/public/index.html` |
| **Feature** | Environmental LF/US `micDiff` burst → sustained extreme shriek variance |

## Detection rule

1. Continuous mic FFT (16384) while armed / Signal on / sudden autorotate.
2. Band energy only: **f &lt; 20 Hz** and **f &gt; 17 kHz** (to Nyquist/23k). Mid-band ignored for onset.
3. Output-aware subtraction (best-effort; not full AEC on iOS Chrome):

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
