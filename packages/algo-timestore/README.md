# algo-timestore

Standalone ASP timestore package (issue **#20**).

Owns the **≥16-parameter SciPy** nonlinear diurnal/year fit, uniqueness quantum
**0.0006** s, non-PII cipher tags, and Fairfax County weather prior (no street
addresses).

**Canonical source** is this tree. ADK deploy only ships
`services/autoroute-adk/iot_asp_autoroute/`, so a vendored copy lives at
`iot_asp_autoroute/algo_timestore/` (synced via
`bash scripts/sync_algo_timestore_to_adk.sh`; verify with `--check`).

## Spec

| Concept | Value |
|---------|--------|
| Circle | 24 h diurnal fraction ∈ [0, 1) |
| Horizon | POSIX now → +1 year |
| Quantum | **0.0006** s |
| Engine | `scipy.optimize.curve_fit` 16 params |
| Weather | Fairfax County VA centroid via Open-Meteo (offline climate fallback) |
| Ciphers | Blake2b tags over source-registered opaque experiment IDs |

## Local sim

```bash
python3 packages/algo-timestore/scripts/sim_fit.py
```

Optional live weather (network):

```bash
IOT_ASP_TIMESTORE_FETCH_WEATHER=1 python3 packages/algo-timestore/scripts/sim_fit.py
```

## Layout

- `algo_timestore/` — library
- `scripts/sim_fit.py` — offline MVP dry-run
- `data/` — reserved for fixtures (no PII)

Autoroute imports the **vendored** subpackage via relative import in
`iot_asp_autoroute/timestore.py` (`from . import algo_timestore`) — no monorepo
`sys.path` hack. The prior bundle includes circle/quantum context, and every
ingested telemetry record receives a protected timestore sidecar.

Edit here first, then:

```bash
bash scripts/sync_algo_timestore_to_adk.sh
bash scripts/adk_layout_import_smoke.sh
```
