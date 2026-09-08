# FIX-F1 — frontend SyntaxError + contract clamp align

| Field | Value |
|-------|--------|
| **Fixed UTC** | `2026-09-08T00:18:45Z` |
| **Repo** | `/Users/machine/apps/IoT-ASP` (+ mirror `hop-ultrasonic/public/index.html`) |
| **Refs** | `.vv/red/FAIL.md` F1/F2/F8; `.vv/red/contract-verify.md` C13/C16/C17 |
| **Vercel prod** | **not** promoted |

---

## 1. F1 / C16 — duplicate `const telSensOrient` (CRITICAL)

### Before

```js
  const telSensOrient = $("telSensOrient"), telSensLight = $("telSensLight");  // ~L494
  const telNight = $("telNight"), telHwBand = $("telHwBand"), telNet = $("telNet");
  const telBand = $("telBand"), telLf = $("telLf"), telPower = $("telPower");
  const telSensOrient = $("telSensOrient"), telSensLight = $("telSensLight");  // DUPLICATE ~L497
  const armSensorsBtn = $("armSensorsBtn");
```

`node --check` (extracted IIFE):

```text
SyntaxError: Identifier 'telSensOrient' has already been declared
```

Entire main script dead → Hold / telemetry / `clampPatch` / poll unreachable.

### After

```js
  const telSensOrient = $("telSensOrient"), telSensLight = $("telSensLight");  // kept (single)
  const telNight = $("telNight"), telHwBand = $("telHwBand"), telNet = $("telNet");
  const telBand = $("telBand"), telLf = $("telLf"), telPower = $("telPower");
  const armSensorsBtn = $("armSensorsBtn");
```

- `const telSensOrient` count: **1** (IoT-ASP + hop-ultrasonic)
- `node --check` extracted script: **exit 0** (both mirrors)

---

## 2. C17 / F8 — FE `clampPatch` ↔ api-contract

Aligned `clampPatch` and local suddenFreq / vib jitter to backend `clamps.py` / `docs/api-contract.md`:

| Param | Before (FE) | After (FE = contract/BE) |
|-------|-------------|---------------------------|
| `pulseMs` | 40–**220** | **20–200** |
| `shriekMs` | 30–120 | **20–120** |
| `vibThreshold` | 0.02–0.8 | **0.01–2.0** |

Sites updated in `public/index.html` (and hop mirror): `clampPatch`, `autorotateOnSudden` jitter, and (IoT-ASP) `routeFromVib` infra_felt nudge.

---

## 3. C13 / F2 — default dry-run includes `vol>100` refuse

Package path (`scripts/autoroute_dev.sh` → `python3 -m iot_asp_autoroute.dry_run`) runs `_assert_clamp_negatives()`:

- `vol=50` → **accept** (`vol_hard_max=100`)
- `vol=0.5` → normalize → **50.0** accept
- `vol=101` → **refuse** (`hard max`)
- OOB `fMin` → refuse

Fallback heredoc in `autoroute_dev.sh` matches the same policy (no stale “hard max 20” / `assert not ok` on `vol=50`).

### Evidence

```text
bash scripts/autoroute_dev.sh
… clamp negatives: OK (vol 50/legacy 0.5 accept; vol 101 + OOB fMin refuse)
… DRY-RUN OK
exit 0
```

---

## Promotion gate

Do **not** `vercel --prod` until this FIX is accepted and Hold/poll re-checked in browser. SEBoK plan not edited.
