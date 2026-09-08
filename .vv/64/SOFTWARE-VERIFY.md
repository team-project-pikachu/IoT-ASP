# #64 — Software-only verify evidence (Balanced PR7)

**Date (UTC):** 2026-09-08T05:11:54Z
**Revision:** `0e40d37` (feat/balanced-api-contract-vv tip at evidence capture)
**Honesty:** marks **CI-verifiable** procedures only. Does **not** claim matrix `pass` for field lab / HW rows.

## Observed command results

### `python3 -m pytest tests/test_api_contract.py tests/test_fleet_log.py tests/test_public_html.py tests/test_ruleset_json.py -q`

- **exit_code:** `0` → PASS

```
........................................................................ [ 48%]
........................................................................ [ 96%]
......                                                                   [100%]
150 passed in 0.78s
```

### `bash scripts/ci_static_gates.sh`

- **exit_code:** `0` → PASS

```
no API key patterns in public/index.html OK
patch.json schemaVersion=1 OK
clamps SCHEMA_VERSION=1 vol_hard_max=100.0 OK
OK ci_static_gates
```

### `bash scripts/autoroute_dev.sh`

- **exit_code:** `0` → PASS

```
wrote /Users/machine/apps/IoT-ASP-wt-balanced-pr7/.autoroute-dry/meta/patches/node1.json
{
  "algo": "burst",
  "band": "17-23k",
  "createdAt": "2026-09-08T05:10:47Z",
  "engineId": "iot-asp-autoroute",
  "fMax": 23000.0,
  "fMin": 17000.0,
  "lfDriveCapable": false,
  "literature": [
    "arxiv:2307.01775",
    "arxiv:2509.17986",
    "arxiv:2211.03647",
    "doi:10.1121/1.5063819"
  ],
  "nodeId": "node1",
  "priorNotes": "- sudden_freq: Sudden frequency onset (\u0394f or energy spike in-band): autorotate noise params (algo cycle + dwell/pulse/shriek jitter) then author a clamped GCS patch for the node.\n- linearized_acoustic: From compressible Navier\u2013Stokes under small perturbations \u2192 linearized acoustic wave equation (1/c0^2)\u2202t\u00b2p' \u2212 \u2207\u00b2p' = S (Lighthill-type sources). Near-ultrasonic air path 17\u201323 kHz is weakly nonlinear at residential gain; band limits are hard constraints. Cite arXiv:2307.01775, arXiv:2509.17986.\n- navier_stokes_constraint: Do NOT claim full Navier\u2013Stokes / CFD on-device. Use linearized acoustics and coupling analogies as soft priors only (docs/physics.md).\n- structure_borne: Structure-borne / seismo-acoustic coupling: chair/floor frames transmit broadband vibration; prefer pulse/shriek/burst over continuous hop when vibClass=physical. Cite arXiv:2211.03647 (seismo-acoustic nuisance) + seated WBV human\u2013seat PMIDs (e.g. 27780424).",
  "priorWeights": {
    "am_gate": 0.25,
    "burst": 0.4,
    "shriek_chirp": 0.35
  },
  "priors": [
    "sudden_freq",
    "linearized_acoustic",
    "navier_stokes_constraint",
    "structure_borne"
  ],
  "pulseMs": 90.0,
  "rationale": "suddenFreq autorotate for node1 @ 19500 Hz; vibClass=physical; band=17-23k; bandBurst=none; weights\u2192burst among ['burst', 'shriek_chirp', 'am_gate']; NS/linearized/seismo priors as constraints only",
  "schemaVersion": 1,
  "seedAction": "keep",
  "shriekMs": 55.0,
  "trigger": "suddenFreq",
  "vibThreshold": 0.15,
  "vol": 100.0
}

DRY-RUN OK
OK fleet_log jsonl
```

## Mapped rows (status → `in_progress`, not `pass`)

| Req ID | Software verify | Evidence |
|--------|-----------------|----------|
| C1-BT | `navigator.bluetooth` absent in `public/index.html` | `tests/test_api_contract.py`, `test_public_html.py` |
| C4-VOL | `vol_hard_max==100` + HTML vol path | CI autoroute job + `ci_static_gates.sh` |
| C5-120V | telemetry `power: "ac120"` | `test_public_html` / e2e payload |
| SCH1 | `schemaVersion: 1` + required `ts` | `test_api_contract`, `test_public_html` |
| HOLD1 | Hold/Manual freezes remote apply | e2e Hold test + static gates |
| I12-R2 | beacon fields + no keys in HTML | `test_api_contract`, static gates |
| GYRO1 | `rotationRate` deg→rad; omit axes until sampled | `test_api_contract`, e2e DeviceMotion dispatch |
| PEER1 | per-tab `instanceId` + `hop.tabSeed`; stale peer CSS | e2e peer stale + BroadcastChannel |

## Still owner / lab gated

- C6 LF systems honesty on device
- `#62` 3-phone field checklist
- Full matrix `pass` rows after evidence packs under `.vv/`
