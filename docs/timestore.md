# Timestore (24 h circle · year quantum)

ASP package for time-indexed carrier / vib samples. **No site PII.**

## Spec (v0)

| Concept | Value |
|---------|--------|
| Circle | 24 h diurnal index (local schedule + UTC `ts`) |
| Horizon | POSIX now → **+1 year** |
| Timestamp uniqueness quantum | **0.0006** s (sub-ms class uniqueness for event keys) |
| Engine | Non-linear ≥16-parameter SciPy fit (backend) — frontend only stamps `ts` / band tags |
| Vib companion | [vib_anomaly.py](../services/autoroute-adk/iot_asp_autoroute/vib_anomaly.py) at **1 Hz**, quantum **0.0005** g |
| Optional LF band | Telemetry `band=10-20` when LF drive armed ([algorithms.md](algorithms.md)) |

## Code

- Stub: `services/autoroute-adk/iot_asp_autoroute/timestore.py`
- Full ≥16-param SciPy + cipher/weather hooks → GitHub Project issues (not blocking Vercel)

## Prior art

Follow [.cursor/rules/asp-prior-art.mdc](../.cursor/rules/asp-prior-art.mdc) before expanding this package.
