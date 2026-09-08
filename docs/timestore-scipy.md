# Timestore SciPy MVP (#20)

Standalone package path (collision-safe vs ADK service):
[`packages/algo-timestore/`](../packages/algo-timestore/).

## Why a separate package

Hybrid ADK work under `services/autoroute-adk/` proceeds in parallel (Claude /
other PRs). Timestore SciPy fit, ciphers, and Fairfax weather priors ship here
first; a thin ADK import can wire later without blocking this MVP.

## Spec

| Concept | Value |
|---------|--------|
| Circle | 24 h diurnal fraction UTC |
| Horizon | POSIX now → **+1 year** |
| Quantum | **0.0006** s |
| Fit | `scipy.optimize.curve_fit` with **16** params (mean + 7 harmonic pairs + drift) |
| Weather | Fairfax County VA **county centroid** via Open-Meteo; default **climate fallback** offline |
| Ciphers | Blake2b-64 tags over non-PII experiment labels |
| PII | **No** street addresses in stamps or weather payloads (`streetAddress: null`) |

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
