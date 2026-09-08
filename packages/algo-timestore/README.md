# algo-timestore

Standalone ASP timestore package (issue **#20**).

Owns the **≥16-parameter SciPy** nonlinear diurnal/year fit, uniqueness quantum
**0.0006** s, non-PII cipher tags, and Fairfax County weather prior (no street
addresses). Does **not** live under `services/autoroute-adk/` so hybrid ADK
work can proceed in parallel.

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

Autoroute consumes this package through
`services/autoroute-adk/iot_asp_autoroute/timestore.py`: the prior bundle
includes circle/quantum context, and every ingested telemetry record receives a
protected timestore sidecar.
