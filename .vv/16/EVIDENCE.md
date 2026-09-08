# Issue #16 — V&V evidence (NS / seismo-acoustic priors)

**Configuration item:** [IoT-ASP#16](https://github.com/team-project-pikachu/IoT-ASP/issues/16)  
**Wave:** IoT-ASP SEBoK e2e plan todo `exec-16-priors`  
**Revision (working tree base):** `e41c3c0e76ef9e0d9ddb59995cc7faf769a8bb79`  
**Verified:** 2026-09-08 (UTC) via `python3 .vv/16/verify_priors.py`  
**Project Done / board:** deferred to integrate lane (this lane does not move Project status)

## Requirements capture

| Req ID | Source | Statement |
|--------|--------|-----------|
| REQ-16-R1 | Issue #16 | Linearized acoustic / NS-derived + seismo-acoustic priors inform vib→algo routing |
| REQ-16-R2 | Issue #16 | Wire priors into autoroute prompt/tools when Gemini/ADK path exists |
| REQ-16-R3 | Issue #16 / physics.md | Cite real arXiv/PubMed/DOI IDs (no fabricated cites) |
| REQ-16-R4 | DESIGN_CONSTRAINTS C6 | Gate optional LF 10–20 Hz / infra_felt TX when `lfDriveCapable` |
| REQ-16-R5 | Plan | Synthetic fixtures + negative control; evidence under `.vv/16/` |

## Verification (built right)

| Procedure | Evidence | Result |
|-----------|----------|--------|
| Prior coefficients in worker (`VIB_ALGO_WEIGHTS`) | `services/autoroute-adk/iot_asp_autoroute/priors.py` | PASS — REQ-16-03 |
| Tool `seismo_acoustic_priors` returns weights + citations | `.vv/16/artifacts/verify_summary.json` | PASS — REQ-16-01/02 |
| Patch author embeds `priors`, `priorWeights`, `literature` | `.vv/16/artifacts/patch_*.json` | PASS — REQ-16-08/12/18 |
| Docs cite DOI/arXiv | `docs/physics.md` literature table | PASS |
| Agent instruction requires priors tool + cites | `iot_asp_autoroute/agent.py` | PASS (static) |
| Offline dry-run still OK | `PYTHONPATH=services/autoroute-adk IOT_ASP_AUTOROUTE_DRY_RUN=1 python3 -m iot_asp_autoroute.dry_run` | PASS |

## Validation (right system)

| Scenario | Fixture | Observed | Result |
|----------|---------|----------|--------|
| Structure-borne physical → burst-family | `fixtures/synthetic_physical.json` | algo=`burst`, band=`17-23k`, prior `structure_borne` | PASS |
| infra_felt + capable → LF gated | `fixtures/synthetic_infra_felt_capable.json` | algo=`infra_mod`, band=`10-20`, f∈[10,20] | PASS |
| infra_felt without capability | `fixtures/synthetic_infra_felt_incapable.json` | stays `17-23k`; no LF claim | PASS |
| **Negative:** nonsense priors / vibClass | `fixtures/negative_nonsense_priors.json` | bogus keys dropped; vib→`none` weights; no CFD claim keys | PASS |

## Artifacts

- `verify_priors.py` — automated checks REQ-16-01…18  
- `fixtures/` — synthetic + negative control telemetry  
- `artifacts/verify_summary.json` — machine-readable pass/fail  
- `artifacts/patch_*.json` — authored patches under each scenario  

## Honesty / non-claims

- No on-phone full Navier–Stokes / CFD.  
- No true infrasound mic/TX without `lfDriveCapable`.  
- No Vercel e2e in this lane (RED owns).  
- No Project 5 Status → Done (integrate lane).

## Re-run

```bash
cd /Users/machine/apps/IoT-ASP
python3 .vv/16/verify_priors.py
```
