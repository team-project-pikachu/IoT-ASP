# API contract — static frontend ↔ GCP/ADK backend

**Version:** `schemaVersion: 1`  
**Scope:** Decoupled control plane between the Vercel static app (`public/`) and the GCP/ADK autoroute stack (`services/autoroute-adk/`).

## Invariants

1. The **frontend only polls/applies patches** and optionally **POSTs/beacons telemetry**. It never embeds Gemini/Vertex API keys, ADK agent code, or Vertex client logic.
2. The **backend** owns ingest → GCS → ADK/Gemini → clamped `patch.json`. Frontend change ≠ backend redeploy and vice versa.
3. No site PII (addresses, names, speech) in telemetry or public artifacts.
4. Phone TX audio is **iOS native A2DP only** (not Web Bluetooth). See [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md).
5. Fleet power assumption: **continuous 120 V AC** (**C5**) — patches must not encode battery-save duty cycles.
6. Optional LF TX: telemetry `band` is `10-20` or `17-23k` (**C6**).

## Endpoints (frontend view)

| Role | Method | Default offline | Live override |
|------|--------|-----------------|---------------|
| Param patch | `GET` | `/patch.json` (static mock on Vercel) | `?patch=<absolute-or-path URL>` or `BACKEND_*` constants in `public/index.html` |
| Telemetry | `POST` / `sendBeacon` | disabled (empty URL) | `?telemetry=<ingest URL>` or `BACKEND_TELEMETRY_URL` |

Poll interval: **default 3000 ms**, clamped **2–5 s** (`?pollMs=` or `BACKEND_POLL_MS_DEFAULT`).  
Poll is **continuous** for the life of the page (`setInterval`); fetch errors set status `offline` but **do not stop** the interval.  
**Hold / Manual** freezes remote patch apply; local `suddenFreq` rotate may continue.

### Hot-apply vs HTML deploy (do not confuse)

| Change | Client behavior | Manual refresh? |
|--------|-----------------|-----------------|
| Engine / autoroute params (`patch.json`, GCS live URL, Gemini/ADK write, dry-run mock) | Polled + **hot-applied in-session** via `applyPatch` (algo / vol / bands / dwell / seedAction). **No** `location.reload`. | **No** — wait ≤ one poll (~2–5 s) |
| Frontend HTML / CSS / JS deploy (`public/index.html`, Vercel) | New shell only after a normal navigation | **Yes — once** after deploy |

Patch fetch uses `cache: "no-store"` plus `_cb=<epoch>` cache-bust. Vercel sets `Cache-Control: no-store` on `/patch.json`. There is **no** service worker; do not add one that network-falls-back-caches `index.html` over patch without an explicit network-first rule for `/patch.json`.

Backend HTTP surface (independent of Vercel):

| Role | Surface | Notes |
|------|---------|--------|
| Ingest | Cloud Run / Cloud Functions (`ingest_main.py`) | Writes `meta/telemetry/<deviceId>/<ts>.json` |
| Patch object | GCS (or signed/CDN URL the phone polls) | `meta/patches/<deviceId>.json` |
| Agent | ADK Agent Engine / Cloud Run | Authors patches; see [adk-autoroute.md](adk-autoroute.md) |

## Telemetry POST / beacon schema (`schemaVersion: 1`)

Compact JSON heartbeat. Required fields marked ★.

```json
{
  "schemaVersion": 1,
  "deviceId": "node1",
  "ts": "2026-09-07T23:00:00Z",
  "seed": 42,
  "algo": "hop",
  "peakHz": 19500,
  "suddenFreq": true,
  "suddenFreqMeta": { "flux": 12.4, "bandDb": -42.0 },
  "suddenAuto": true,
  "suddenState": "rotate",
  "geminiAutorouteFlag": true,
  "event": "suddenFreq",
  "absA": 0.12,
  "ax": 0.05,
  "ay": -0.02,
  "az": 0.11,
  "absOmega": 0.4,
  "gx": 0.1,
  "gy": -0.2,
  "gz": 0.3,
  "micEnergy": -42.0,
  "outLevel": -55.0,
  "micDiff": 13.0,
  "bandEnergyLf": -70.0,
  "bandEnergyUs": -48.0,
  "bandBurst": "us",
  "soundBurst": false,
  "extremeActive": false,
  "impulse": false,
  "volBlast": false,
  "alarmState": "armed",
  "audioContextState": "running",
  "materialPreset": "table",
  "fMin": 17000,
  "fMax": 23000,
  "band": "17-23k",
  "lfDriveCapable": false,
  "lfArmed": false,
  "power": "ac120",
  "nightNY": false,
  "vol": 100,
  "pulseMs": 80,
  "shriekMs": 50,
  "vibThreshold": 0.15,
  "vibClass": "physical",
  "holdManual": false
}
```

| Field | ★ | Type | Notes |
|-------|---|------|--------|
| `schemaVersion` | ★ | `1` | Wire format version |
| `deviceId` | ★ | string | Stable per browser (`localStorage`) |
| `ts` | ★ | ISO-8601 or epoch ms | Ingest normalizes filenames |
| `band` | | string | `17-23k` (default) \| `10-20` when LF armed |
| `lfDriveCapable` | | bool | Systems/capability gate for LF |
| `lfArmed` | | bool | User armed optional 10–20 Hz path |
| `power` | | string | `ac120` continuous mains (fleet invariant) |
| `nightNY` | | bool | Inside 22:00–07:00 America/New_York volume curve |
| `algo` | ★ | wire name | `hop` \| `am_gate` \| `shriek_chirp` \| `shriek_sweep` \| `burst` \| `infra_mod` \| `cry_mirror` \| `siren_mirror` \| `death_metal_mirror` |
| `suddenFreq` | ★ | bool | Primary autorotate trigger when true |
| `suddenState` | | string | `idle` \| `onset` \| `rotate` \| … |
| `geminiAutorouteFlag` | | bool | UI flag: remote patch desired after local rotate |
| `event` | | string | Optional alias; `suddenFreq` \| `soundBurst` accepted |
| `absA` / `a` | | number | Accel magnitude (g); either key; derived from `ax,ay,az` when missing |
| `ax` / `ay` / `az` | | number | Optional linear accel axes (g) |
| `absOmega` / `omega` | | number | Gyro magnitude (rad/s); either key; derived from `gx,gy,gz` when missing |
| `gx` / `gy` / `gz` | | number | Optional gyro axes (rad/s) |
| `micEnergy` | | number | Mic energy (dB or linear — stored as sent) |
| `outLevel` | | number | TX / out level used in micDiff (same units as micEnergy) |
| `micDiff` | | number | `micEnergy − α·outLevel` (α≈0.85); burst/extreme keys off this when present |
| `micNet` | | number | Alias of `micDiff` (frontend burst path) |
| `bandEnergyLf` | | number | Mic/spectrum energy for **f &lt; 20 Hz** |
| `bandEnergyUs` | | number | Mic/spectrum energy for **f &gt; 17 kHz** (to Nyquist / 23 k) |
| `bandBurst` | | string | `lf` \| `us` \| `both` \| `none` — which extreme band triggered |
| `soundBurst` | | bool | Environmental energy onset (sustained while true) |
| `soundBurstMeta` | | object | Optional `{ energyDelta, baselineDb, onsetDb, micDiff, … }` |
| `extremeActive` | | bool | Extreme variance mode active until quiet hysteresis |
| `impulse` | | bool | Short micDiff rise/peak or accel spike detected (latched briefly) — #44 |
| `volBlast` | | bool | Alarm blast: vol jumped toward max within night/Hold rules — #44 #45 |
| `alarmState` | | string | `armed` \| `triggered` \| `sustaining` \| `cleared` \| `off` — #45 |
| `audioContextState` / `ctxState` | | string | Either key |
| `vol` | | number | **UI percent 0–100** (matches slider max); legacy linear ≤1 accepted by ingest/author |
| `holdManual` | | bool | If true, backend must refuse patches |
| `vibClass` | | string | `none` \| `physical` \| `acoustic` \| `infra_felt` |
| `materialPreset` | | string | `handheld` \| `table` \| `chair` \| `speaker` — material → channel arming (#6); soft algo bias via `MATERIAL_CHANNEL_BIAS` |
| `band` | | string | `17-23k` (default) \| `10-20` (LF, only with `lfDriveCapable`) — #22 |
| `power` | | string | `ac120` (fleet is continuous 120 V AC) — #22 |
| `nightNY` | | bool | Local hour in America/New_York ∈ [22, 07) — #22 |
| `lfArmed` / `lfDriveCapable` | | bool | LF 10–20 Hz TX arm + hardware capability; web fleet defaults `false` — #22/#25 |
| `lastHopAgeMs` / `ctxResumes` / `watchdogTrips` | | number | Watchdog health counters — #3 |
| `logSeq` / `logTail` | | number / array | Structured monitor-log sequence + last 3 records (`{seq, ts, level, event, msg, fields}`, no PII) — #22 |
| `ax` `ay` `az` / `accelAxes` | | number / [3] | Linear acceleration axes (g) when available — #26 |
| `gx` `gy` `gz` / `gyroAxes` | | number / [3] | Rotation-rate axes (deg/s) when available — #26 |
| `outLevel` | | number | Output bus level (dB) used for `micDiff` — #25/#26 |
| `micDiff` | | number | `micEnergy − 0.85·outLevel` (best-effort AEC; browser cannot do full AEC) — #25 |
| `bandBurst` | | string | `lf` \| `us` \| `both` burst classification — #25/#26 |
| `soundBurst` / `extremeActive` | | bool | Environmental burst detected / sustained extreme shriek mode — #25 |
| `impulse` | | bool | Short-rise accel or micDiff onset this cycle — #42/#44 |
| `volBlast` | | bool | Alarm/impulse jumped volume toward max — #42/#44 |
| `alarmState` | | string | `armed` \| `triggered` \| `sustaining` \| `cleared` \| `off` — #42/#45 (Hold→cleared, suddenAuto off→off via effectiveAlarmState) |
| `lfEnergy` / `usEnergy` | | number | LF (<20 Hz proxy) and US (>17 kHz) band energy (dB) — #25 |

Backend enrichment (`fleet_log.enrich_telemetry`) fills `band`, `power`, `nightNY`, `lfArmed`,
`lfDriveCapable` when the phone omits them, and derives `lfGate = lfArmed ∧ lfDriveCapable ∧ vibClass == infra_felt`.
Structured records land in `meta/logs/<deviceId>/<YYYY-MM-DD>.jsonl`; sensor feature records
(`features_live.run_live`) land in `meta/features/<deviceId>/<ts>.json` and are never authoritative.

Additive sensor/burst fields are **optional** on the wire (`schemaVersion` stays `1`). Colab ETL + ADK project them when present; consumers ignore unknown keys.

**Storage:** `gs://<private-bucket>/meta/telemetry/<deviceId>/<ts>.json`

## Param patch JSON schema (`schemaVersion: 1`)

```json
{
  "schemaVersion": 1,
  "algo": "am_gate",
  "fMin": 17000,
  "fMax": 21000,
  "vol": 100,
  "pulseMs": 100,
  "shriekMs": 60,
  "vibThreshold": 0.12,
  "seedAction": "keep",
  "rationale": "suddenFreq + max practical Web Audio gain (BT/hardware limit SPL)",
  "priors": ["sudden_freq", "linearized_acoustic"],
  "engineId": "iot-asp-autoroute",
  "createdAt": "2026-09-07T23:00:00Z",
  "trigger": "suddenFreq",
  "nodeId": "node1"
}
```

| Field | ★ | Type | Notes |
|-------|---|------|--------|
| `schemaVersion` | ★ | `1` | Consumers may ignore unknown newer fields |
| `algo` | ★ | whitelist | Same wire names as telemetry |
| `fMin` / `fMax` | | Hz | Ultrasonic ∈ [17000, 23000] **or** LF ∈ [10, 20] when `band=10-20`; `fMin` < `fMax` |
| `band` | | string | `17-23k` default; `10-20` only when `lfDriveCapable` + infra_felt path |
| `vol` | | number | **UI percent**; soft==hard ≤100 (max practical Web Audio) |
| `pulseMs` | | ms | 20–200 |
| `shriekMs` | | ms | 20–120 |
| `vibThreshold` | | number | 0.01–2.0 |
| `seedAction` | | string | `keep` \| `reseed` |
| `rationale` | | string | Shown in monitor log (no PII) |
| `priors` | | string[] | Known prior keys only (`sudden_freq`, `linearized_acoustic`, `structure_borne`, `infra_felt`, …); nonsense keys ignored |
| `priorWeights` | | object | Optional vib→algo soft weights used by author |
| `literature` | | string[] | Optional cite IDs (arXiv/DOI/PMID) from priors bundle |
| `engineId` | | string | Default `iot-asp-autoroute` |
| `trigger` | | string | e.g. `suddenFreq` |
| `burstBias` | | object | `{"micDiffDb": number \| null, "shriekMsBias": 15}` — present only when an environmental burst (`soundBurst` / `extremeActive` / `micDiff` > 6 dB, never under `holdManual`) biased `algo` → `shriek_chirp`; phones ignore unknown keys — #25 |

**Write:** `gs://<private-bucket>/meta/patches/<deviceId>.json`  
**Offline mock:** `public/patch.json` on Vercel (no Gemini).

Frontend algo UI aliases: `pulse` ↔ `am_gate`, `shriek` ↔ `shriek_chirp`, `cry` ↔ `cry_mirror`, `siren` ↔ `siren_mirror`, `metal` / `metal_mirror` ↔ `death_metal_mirror`. Backend always emits wire names. Contour-mirrors (`cry_mirror`, `siren_mirror`, `death_metal_mirror`) are **generative Web Audio contour synthesis** within the TX band — not copyrighted samples or recordings.

## Safety clamps (backend must enforce before write)

See [autoroute.md](autoroute.md). Parser fallback on the phone is defense-in-depth only — not a substitute for worker clamps.

## Decoupling checklist

| Change | Touch frontend? | Touch backend? | Redeploy |
|--------|-----------------|----------------|----------|
| ADK prompt / tools / clamps | No | Yes | Cloud Run / Agent Engine only |
| Telemetry ingest URL | Optional (`?telemetry=` / constants) | Yes if handler changes | Backend; Vercel only if HTML constants changed |
| Patch field semantics | Only if breaking `schemaVersion` | Bump `schemaVersion` + clamps | Both if wire break; prefer additive fields |
| UI / Web Audio / copy | Yes | No | Vercel only |
| Dry-run | No | Local | `bash scripts/autoroute_dev.sh` |

## Related docs

- [autoroute.md](autoroute.md) — control-loop intent + clamps narrative  
- [adk-autoroute.md](adk-autoroute.md) — independent ADK/Cloud Run deploy  
- [gcp-recordings.md](gcp-recordings.md) — private GCS recordings + `meta/` layout  
- [gemini-enterprise.md](gemini-enterprise.md) — seats / engine id (credential **names** only)
