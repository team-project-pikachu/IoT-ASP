# Colab ↔ Gemini Enterprise ↔ ADK pipeline

Offload heavy ETL to **Google Colab** (paid tier; account per `google-colab-etl` skill). Pair with **Gemini Enterprise (5 seats)** and the **ADK autoroute agent**.

**Issue:** [#17](https://github.com/team-project-pikachu/IoT-ASP/issues/17)  
**Shared SciPy module:** `services/autoroute-adk/iot_asp_autoroute/vib_anomaly.py` (1 Hz preferred, quantum **0.0005 g**)  
**Shared feature builder:** `services/autoroute-adk/iot_asp_autoroute/colab_etl.py`  
**Contract:** [api-contract.md](api-contract.md) `schemaVersion: 1`

## Flow

```
phones (telemetry + optional .webm)
    → private GCS (project bear-iot-asp-rec)
    → Colab ETL (spectra, vib features, NS/seismo priors as features — not CFD)
    → Gemini Enterprise (engine iot-asp-autoroute) interpretation / synthesis
    → ADK agent validates clamps + writes meta/patches/<nodeId>.json
    → nodes poll patches; study notes stay private
```

Colab never writes authoritative patches. It may emit **suggestions** only; ADK/`validate_patch` remains the write gate.

## Starter notebook

`notebooks/iot_asp_colab_etl.ipynb` (+ markdown twin `notebooks/iot_asp_colab_etl.md`):

| Cell group | Behavior |
|------------|----------|
| Offline dry-run | Imports `colab_etl` + `vib_anomaly` from the ADK package; no network |
| Feature extract | Projects telemetry onto **api-contract** columns; derives `priorHint` + sensor bundle |
| Synthetic vib+gyro+sound | `sample_vib_gyro_sound_fixture` — accel axes, ω, micDiff, LF/US band energies, burst flags |
| SciPy anomaly | Shared `detect_disturbances` / `detect_from_telemetry_points` at 1 Hz |
| Patch stub | `suggest_patch_stub` — Hold/Manual refuses; shriek bias on burst; clamps defensive |
| Live GCS (Colab) | Auth via `userdata.get('GCP_SA_JSON')` only; gated behind `LIVE_GCS=1` |

Offline verification (repo root):

```bash
python3 scripts/colab_etl_dry_run.py
python3 -m iot_asp_autoroute.dry_run_anomaly   # from services/autoroute-adk
```

## Feature columns (must match telemetry contract)

Canonical heartbeat fields projected into `meta/features/<deviceId>/…`:

`schemaVersion`, `deviceId`, `ts`, `seed`, `algo`, `peakHz`, `suddenFreq`, `suddenFreqMeta`, `suddenAuto`, `suddenState`, `geminiAutorouteFlag`, `event`, `absA` (alias `a`), `ax`/`ay`/`az`, `absOmega` (alias `omega`), `gx`/`gy`/`gz`, `micEnergy`, `outLevel`, `micDiff`, `bandEnergyLf` (f&lt;20 Hz), `bandEnergyUs` (f&gt;17 kHz), `bandBurst` (`lf`\|`us`\|`both`\|`none`), `soundBurst`, `soundBurstMeta`, `extremeActive`, `audioContextState` (alias `ctxState`), `materialPreset`, `fMin`, `fMax`, `band` (`17-23k` \| `10-20`), `lfDriveCapable`, `lfArmed`, `power`, `nightNY`, `vol`, `pulseMs`, `shriekMs`, `vibThreshold`, `vibClass` (`none` \| `physical` \| `acoustic` \| `infra_felt`), `holdManual`.

Derived (not on the wire as-is): `priorHint`, `derived.sensors` (accel/gyro/micDiff/bandBurst/shriekBiasEligible), anomaly summary (`disturbance`, `peaks`, `mad`), `vibQuantumG`, `sampleHz`.

### Accel / gyro / mic-spectrum ETL

| Channel | Wire / GCS fields | Colab derived |
|---------|-------------------|---------------|
| Accelerometer | `absA` / `a`, optional `ax,ay,az` | `accelMagG`, axes-present flag; SciPy vib anomaly on \|a\| series |
| Gyroscope | `absOmega` / `omega`, optional `gx,gy,gz` | `gyroMagRadS`; gyroBurst heuristic |
| Mic / spectrum | `micEnergy`, `outLevel`, `micDiff`, `bandEnergyLf`, `bandEnergyUs` | `micDiff = micEnergy − α·outLevel` (α=1) when not precomputed; quantized 0.1 |
| Burst flags | `soundBurst`, `extremeActive`, `bandBurst` | `shriekBiasEligible` → patch stub prefers shriek/burst |

Offline synthetic fixture: `sample_vib_gyro_sound_fixture()` in `colab_etl.py` (notebook cell **2b**).

Patch **suggestions** bias shriek/extreme when `soundBurst` / `extremeActive` / LF·US band / vib·gyro bursts; ADK still clamps before any `meta/patches/` write.

## SciPy anomaly path (Colab = ADK)

| Item | Value |
|------|--------|
| Module | `iot_asp_autoroute.vib_anomaly` |
| Sample rate | **1 Hz** (browser DeviceMotion beacon rate) |
| Quantum | **0.0005 g** (`VIB_QUANTUM`) |
| Pipeline | `medfilt` baseline → residual → `median_abs_deviation(scale="normal")` → z-score + quantum steps → `find_peaks` |
| Context7 | `/scipy/scipy` — `medfilt` requires odd `kernel_size`; MAD `scale='normal'` ≈ σ for Gaussian |

Do **not** fork a second anomaly implementation in the notebook. Clone/checkout this repo on the Colab VM (or `sys.path` the ADK package) and import the shared module.

## Env / secrets (credential **refs** only)

| Name | Where | Notes |
|------|-------|--------|
| `GCP_SA_JSON` | Colab userdata **only** | Forbidden in git/chat/Studio download |
| `GOOGLE_CLOUD_PROJECT` | env / userdata | Value: `bear-iot-asp-rec` (project id, not a secret) |
| `IOT_ASP_GEMINI_ENGINE_ID` | env / userdata | Default `iot-asp-autoroute` |
| `IOT_ASP_GCS_BUCKET` | userdata / env | Private bucket **name** only |
| `LIVE_GCS` | notebook flag | Set `1` only on Colab when ready to touch GCS |

Never commit SA JSON, private keys, or Discovery Engine API keys. See `services/autoroute-adk/.env.example`.

## GCS layout

| Prefix | Producer | Consumer |
|--------|----------|----------|
| `meta/telemetry/<deviceId>/<ts>.json` | ingest / phone beacon | Colab + ADK |
| `meta/features/<deviceId>/…` | Colab ETL | Gemini seats / ADK tools |
| `meta/colab-jobs/<nodeId>-latest.json` | ADK `colab_handoff_note` | Colab operator |
| `meta/patches/<deviceId>.json` | **ADK only** | phones poll |

## Related

- [gemini-enterprise.md](gemini-enterprise.md)  
- [adk-autoroute.md](adk-autoroute.md)  
- [api-contract.md](api-contract.md)  
- [physics.md](physics.md)  
- [timestore.md](timestore.md) — vib companion quantum  
- Skill: `~/.cursor/skills/google-colab-etl/SKILL.md`  
- Evidence (issue #17): `.vv/17/`
