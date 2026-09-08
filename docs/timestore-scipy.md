# Timestore SciPy MVP (#20)

Canonical library: [`packages/algo-timestore/`](../packages/algo-timestore/).

ADK packaging copy (what `adk deploy … iot_asp_autoroute` ships):
[`services/autoroute-adk/iot_asp_autoroute/algo_timestore/`](../services/autoroute-adk/iot_asp_autoroute/algo_timestore/).

## Why a separate package + vendor copy

The standalone package owns fitting and privacy boundaries. Autoroute includes
time context in routing priors and stamps persisted telemetry via a thin
adapter (`iot_asp_autoroute/timestore.py`) that **relative-imports**
`iot_asp_autoroute.algo_timestore`.

`adk deploy` does **not** include the monorepo `packages/` tree, so the library
is vendored under the agent package and kept in sync with:

```bash
bash scripts/sync_algo_timestore_to_adk.sh          # copy canonical → vendor
bash scripts/sync_algo_timestore_to_adk.sh --check  # CI drift gate
bash scripts/adk_layout_import_smoke.sh            # ADK-only PYTHONPATH smoke
```

## Spec

| Concept | Value |
|---------|--------|
| Circle | 24 h diurnal fraction UTC |
| Horizon | POSIX now → **+1 year** |
| Quantum | **0.0006** s |
| Fit | `scipy.optimize.curve_fit` with **16** params (mean + 7 harmonic pairs + bounded periodic weather response) |
| Weather | Fairfax County VA **county centroid** via Open-Meteo; default **climate fallback** offline |
| Ciphers | Blake2b-64 tags over source-registered opaque experiment IDs |
| PII | **No** street addresses in stamps or weather payloads (`streetAddress: null`) |

The fit result contains parameters, per-parameter uncertainty, residuals, RMSE,
weather metadata/effect magnitude, and a protected timestore stamp.

## Autoroute integration

- `seismo_acoustic_priors()` returns `timestore` circle, horizon, quantum, and fit context.
- `ingest_telemetry()` adds a protected `timestore` sidecar before persistence.

## Local sim

```bash
python3 packages/algo-timestore/scripts/sim_fit.py
```

Live county weather (optional):

```bash
IOT_ASP_TIMESTORE_FETCH_WEATHER=1 python3 packages/algo-timestore/scripts/sim_fit.py
```

## Related

- Issue **#20**
- Vib companion remains ADK `vib_anomaly` (1 Hz / 0.0005 g) — not duplicated here
- Prior art: SciPy `curve_fit` / awesome-list ASP notes
