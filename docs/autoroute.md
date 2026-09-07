# Autoroute — telemetry, patches, clamps

Hybrid control plane for continuous monitoring + continuous audio-engineering parameter updates. **ADK agent** is the patch author (see [adk-autoroute.md](adk-autoroute.md)).

Gemini Enterprise engine: **`iot-asp-autoroute`** on project `bear-iot-asp-rec` ([gemini-enterprise.md](gemini-enterprise.md)).

## Telemetry beacon (v0)

Nodes POST compact JSON (no addresses / no speech):

```json
{
  "deviceId": "node1",
  "ts": "2026-09-07T23:00:00Z",
  "seed": 42,
  "algo": "hop",
  "peakHz": 19500,
  "absA": 0.12,
  "micEnergy": 0.03,
  "audioContextState": "running",
  "fMin": 17000,
  "fMax": 23000,
  "vol": 0.08,
  "pulseMs": 80,
  "shriekMs": 50,
  "vibThreshold": 0.15,
  "vibClass": "physical",
  "holdManual": false
}
```

Store: `gs://<private-bucket>/meta/telemetry/<deviceId>/<ts>.json`

## Param patch schema (v0)

```json
{
  "algo": "am_gate",
  "fMin": 17000,
  "fMax": 23000,
  "vol": 0.08,
  "pulseMs": 100,
  "shriekMs": 60,
  "vibThreshold": 0.2,
  "seedAction": "keep",
  "rationale": "physical vib ↑ → prefer gated pulses; NS prior: structure-borne coupling",
  "priors": ["structure_borne", "linearized_acoustic"],
  "engineId": "iot-asp-autoroute",
  "createdAt": "ISO-8601"
}
```

Allowed `algo`: `hop` | `am_gate` | `shriek_chirp` | `shriek_sweep` | `burst` | `infra_mod` (future).  
`seedAction`: `keep` | `reseed`.

Write: `gs://<private-bucket>/meta/patches/<deviceId>.json`  
Poll interval: **2–5 s**. Human **Hold / Manual** freezes apply.

## Safety clamps (worker must enforce)

| Param | Clamp |
|-------|--------|
| `fMin`/`fMax` | ∈ [17000, 23000], `fMin` < `fMax` |
| `vol` | ≤ 0.12 (residential default); hard refuse > 0.20 |
| `pulseMs` | 20–200 |
| `shriekMs` | 20–120; shriek duty refuse if continuous high |
| `algo` | whitelist only |
| Out-of-policy | refuse patch; log rationale |

Cite VHF/ultrasound human-effects literature in [reference/LITERATURE.md](../reference/LITERATURE.md) (e.g. Fletcher/Leighton JASA DOI `10.1121/1.5063819`) — **not** medical claims.

## Physics priors (prompt/context, not on-phone CFD)

Agent may reason with linearized acoustic / Navier–Stokes–derived wave equations and seismo-acoustic coupling as **constraints** for structure-borne vs air-borne routing — see [physics.md](physics.md). Do **not** claim full CFD on the phone.

## ADK (primary implementation)

- Overview: https://docs.cloud.google.com/agent-builder/agent-development-kit/overview  
- Scaffold: `services/autoroute-adk/`  
- Local: `adk web` or `adk run` from that package  
- Deploy: `adk deploy agent_engine` / `adk deploy cloud_run` → project `bear-iot-asp-rec`, region `us-central1`

## Dev dry-run

```bash
bash scripts/autoroute_dev.sh
```
