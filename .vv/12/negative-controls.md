# Negative controls — Issue #12

Automated inside `python -m iot_asp_autoroute.dry_run` (invoked by `bash scripts/autoroute_dev.sh`).

| Control | Input | Expected | Observed |
|---------|-------|----------|----------|
| Vol mid-range | `vol: 50` | accept; clamped vol `50.0` | PASS |
| Legacy linear | `vol: 0.5` | normalize → `50.0` accept | PASS |
| Vol over hard max | `vol: 101` | refuse (`exceeds hard max 100`) | PASS |
| OOB ultrasonic fMin | `fMin: 1000`, US band | refuse outside [17000,23000] | PASS |
| Hold + suddenFreq author | `holdManual: true` | refuse patch | PASS |
| Hold + process_sudden_freq | latest tel hold | refuse | PASS |
| Hold + write_patch | latest tel hold | refuse even if patch body valid | PASS |
| Disallowed algo (spot) | e.g. `algo: "laser"` | refuse (clamp whitelist) | covered by `validate_patch` / ALLOWED_ALGOS |

**Invariant:** Hold/Manual **must win** over Gemini/heuristic autoroute. Frontend Hold is independent defense-in-depth.
