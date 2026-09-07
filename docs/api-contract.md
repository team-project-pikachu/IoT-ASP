# API contract — static frontend ↔ GCP/ADK backend

**Version:** `schemaVersion: 1`  
**Scope:** Decoupled control plane between the Vercel static app (`public/`) and the GCP/ADK autoroute stack (`services/autoroute-adk/`).

## Invariants

1. The **frontend only polls/applies patches** and optionally **POSTs/beacons telemetry**. It never embeds Gemini/Vertex API keys, ADK agent code, or Vertex client logic.
2. The **backend** owns ingest → GCS → ADK/Gemini → clamped `patch.json`. Frontend change ≠ backend redeploy and vice versa.
3. No site PII (addresses, names, speech) in telemetry or public artifacts.
4. Phone TX audio is **iOS native A2DP only** (not Web Bluetooth). See [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md).

## Endpoints (frontend view)

| Role | Method | Default offline | Live override |
|------|--------|-----------------|---------------|
| Param patch | `GET` | `/patch.json` (static mock on Vercel) | `?patch=<absolute-or-path URL>` or `BACKEND_*` constants in `public/index.html` |
| Telemetry | `POST` / `sendBeacon` | disabled (empty URL) | `?telemetry=<ingest URL>` or `BACKEND_TELEMETRY_URL` |

Poll interval: **2–5 s** (`?pollMs=` clamped).  
**Hold / Manual** freezes remote patch apply; local `suddenFreq` rotate may continue.

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
  "micEnergy": 0.03,
  "audioContextState": "running",
  "materialPreset": "table",
  "fMin": 17000,
  "fMax": 23000,
  "vol": 8,
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
| `algo` | ★ | wire name | `hop` \| `am_gate` \| `shriek_chirp` \| `shriek_sweep` \| `burst` \| `infra_mod` |
| `suddenFreq` | ★ | bool | Primary autorotate trigger when true |
| `suddenState` | | string | `idle` \| `onset` \| `rotate` \| … |
| `geminiAutorouteFlag` | | bool | UI flag: remote patch desired after local rotate |
| `event` | | string | Optional alias; `suddenFreq` accepted |
| `absA` / `a` | | number | Accel magnitude (g); either key |
| `micEnergy` | | number | Mic energy (dB or linear — stored as sent) |
| `audioContextState` / `ctxState` | | string | Either key |
| `vol` | | number | **UI percent 0–12** (matches slider); legacy linear ≤1 accepted by ingest/author |
| `holdManual` | | bool | If true, backend must refuse patches |
| `vibClass` | | string | `none` \| `physical` \| `acoustic` \| `infra_felt` |

**Storage:** `gs://<private-bucket>/meta/telemetry/<deviceId>/<ts>.json`

## Param patch JSON schema (`schemaVersion: 1`)

```json
{
  "schemaVersion": 1,
  "algo": "am_gate",
  "fMin": 17000,
  "fMax": 21000,
  "vol": 8,
  "pulseMs": 100,
  "shriekMs": 60,
  "vibThreshold": 0.12,
  "seedAction": "keep",
  "rationale": "suddenFreq + residential-safe gain",
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
| `fMin` / `fMax` | | Hz | ∈ [17000, 23000], `fMin` < `fMax` |
| `vol` | | number | **UI percent**; soft ≤12, hard refuse >20 |
| `pulseMs` | | ms | 20–200 |
| `shriekMs` | | ms | 20–120 |
| `vibThreshold` | | number | 0.01–2.0 |
| `seedAction` | | string | `keep` \| `reseed` |
| `rationale` | | string | Shown in monitor log (no PII) |
| `engineId` | | string | Default `iot-asp-autoroute` |
| `trigger` | | string | e.g. `suddenFreq` |

**Write:** `gs://<private-bucket>/meta/patches/<deviceId>.json`  
**Offline mock:** `public/patch.json` on Vercel (no Gemini).

Frontend algo UI aliases: `pulse` ↔ `am_gate`, `shriek` ↔ `shriek_chirp`. Backend always emits wire names.

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
- [gemini-enterprise.md](gemini-enterprise.md) — seats / engine id (credential **names** only)
