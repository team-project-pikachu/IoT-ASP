# Autoroute — sudden-frequency → Gemini autorotates noises

**Primary control loop** for IoT-ASP. Hybrid local heuristic + ADK/Gemini patches. See [adk-autoroute.md](adk-autoroute.md).

**Formal API contract (telemetry + patch + `schemaVersion`):** [api-contract.md](api-contract.md). Frontend polls/applies patches only — never embeds Gemini/Vertex keys or ADK logic. Backend (`services/autoroute-adk/`) deploys independently of Vercel `public/`.

**Formal constraints:** [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) — phone TX is **iOS native A2DP only** (not Web Bluetooth). Details: [iphone-bluetooth.md](iphone-bluetooth.md).

Gemini Enterprise engine: **`iot-asp-autoroute`** on project `bear-iot-asp-rec` ([gemini-enterprise.md](gemini-enterprise.md)).

## Intent

**Gemini autorotates the noises based on detection of sudden frequencies.**

1. Continuous mic / spectrum (optional vib) detects **sudden frequency events** (onsets, spikes, band energy jumps).
2. Emit telemetry **`suddenFreq`**; local heuristic rotates TX algo/params immediately.
3. When online, ADK/Gemini authors `patch.json` (unless **Hold / Manual**).
4. Material preset ([materials-engineering.md](materials-engineering.md)) soft-biases channel/algo choice.

```text
Web Audio TX ──► iOS system A2DP ──► Soundcore (1:1 OS route)
mic/analyser/accel
        │
        ▼
 suddenFreq detector (flux / peak jump / energy onset)
        ├─► local rotate (debounce ≥300–400 ms)
        └─► telemetry → GCS → ADK/Gemini → patch.json → poll/apply
```

## Telemetry / patch schemas

Canonical schemas (incl. `schemaVersion`, `suddenFreq`, UI-percent `vol`) live in **[api-contract.md](api-contract.md)**. Do not fork field lists here.

Store telemetry: `gs://<private-bucket>/meta/telemetry/<deviceId>/<ts>.json`  
Write patches: `gs://<private-bucket>/meta/patches/<deviceId>.json`  
Poll interval: **2–5 s**. Human **Hold / Manual** freezes remote apply (local suddenFreq rotate may continue).

Allowed `algo`: `hop` | `am_gate` | `shriek_chirp` | `shriek_sweep` | `burst` | `infra_mod` (future).  
`seedAction`: `keep` | `reseed`.

## Safety clamps (worker must enforce)

| Param | Clamp |
|-------|--------|
| `fMin`/`fMax` | ∈ [17000, 23000], `fMin` < `fMax` |
| `vol` | **UI percent** ≤ 12 (residential soft); hard refuse > 20; legacy linear ≤1 normalized ×100 |
| `pulseMs` | 20–200 |
| `shriekMs` | 20–120; shriek duty refuse if continuous high |
| `algo` | whitelist only |
| Out-of-policy | refuse patch; log rationale |

Cite VHF/ultrasound human-effects literature in [reference/LITERATURE.md](../reference/LITERATURE.md) — **not** medical claims.

## Physics / materials priors

- [physics.md](physics.md) — linearized acoustic / NS / seismo-acoustic
- [materials-engineering.md](materials-engineering.md) — mount presets

Do **not** claim full CFD on the phone. BT latency makes hop timing soft ([iphone-bluetooth.md](iphone-bluetooth.md)).

## ADK (primary implementation)

- Overview: https://docs.cloud.google.com/agent-builder/agent-development-kit/overview
- Scaffold: `services/autoroute-adk/`
- Local: `adk web` or `adk run` · Deploy: `adk deploy agent_engine` / `cloud_run` → `bear-iot-asp-rec` / `us-central1`

## Dev dry-run

```bash
bash scripts/autoroute_dev.sh
```
