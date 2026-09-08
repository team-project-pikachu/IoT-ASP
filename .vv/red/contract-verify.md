# RED — contract / clamps verify

| Field | Value |
|-------|--------|
| **Audit UTC** | `2026-09-08T00:15:04Z` |
| **Revision** | `e41c3c0e76ef9e0d9ddb59995cc7faf769a8bb79` |
| **Repo** | `/Users/machine/apps/IoT-ASP` |
| **Scope** | `clamps.py` ↔ `docs/api-contract.md` ↔ `scripts/autoroute_dev.sh` ↔ `public/` poll / Hold |
| **Plan** | context only (not edited) |
| **Verdict** | **FAIL** — backend clamps + dry-run happy paths green; frontend IIFE does not parse (Hold/poll dead); FE `clampPatch` ranges drift from contract |

Companion adversarial notes: [FAIL.md](FAIL.md), [PASS.md](PASS.md).

---

## Checks

| ID | Check | Result | Evidence |
|----|--------|--------|----------|
| C1 | `SCHEMA_VERSION == 1` matches `api-contract.md` | **PASS** | `clamps.py:27`; contract header `schemaVersion: 1` |
| C2 | `vol` soft==hard **100** (UI %) | **PASS** | `CLAMPS["vol_soft_max"|"vol_hard_max"]=100.0`; contract patch table |
| C3 | `pulseMs` 20–200, `shriekMs` 20–120, `vibThreshold` 0.01–2.0 | **PASS** | `clamps.py:22–24` == contract |
| C4 | Dual bands US [17000,23000] / LF [10,20] | **PASS** | `BAND_US` / `BAND_LF`; `band_limits()`; LF sample `validate_patch` ok |
| C5 | `ALLOWED_ALGOS` wire whitelist | **PASS** | `hop`, `am_gate`, `shriek_chirp`, `shriek_sweep`, `burst`, `infra_mod` |
| C6 | Refuse OOB / bad algo / `fMin≥fMax` / `vol>100` | **PASS** | Probed: `vol=101` refuse; `algo=evil` refuse; `fMin=16000` refuse; `pulseMs=10` refuse |
| C7 | Legacy `vol≤1` → ×100 | **PASS** | `vol=0.5` → `50.0` accepted |
| C8 | Backend `holdManual` refuse before write | **PASS** | `sudden_freq.py:44–45,67–68` → `holdManual — refuse patch` |
| C9 | `api-contract.md` invariants (poll-only FE, no keys, C5/C6) | **PASS** | Doc present; grepped `public/index.html` — no `GEMINI`/`VERTEX`/`API_KEY` |
| C10 | Offline mock `public/patch.json` schema | **PASS** | `schemaVersion:1`, `vol:100`, wire `algo:am_gate`, in-band Hz |
| C11 | `bash scripts/autoroute_dev.sh` primary path | **PASS** | Imports `iot_asp_autoroute.dry_run` → exit 0, `DRY-RUN OK`, patch `vol:100` |
| C12 | Fallback heredoc asserts (when dry_run import skipped) | **PASS** | Forced `sed -n '17,70p' … \| bash` exit 0. Asserts now: `vol=50` OK, `vol=0.5→50` OK, `vol=101` refuse. **Greens already fixed** stale “hard max 20 / assert not ok on vol=50”. |
| C13 | Default dry-run path exercises `vol>hard_max` negative control | **FAIL** | Package `dry_run.py` never calls the refuse assert; script exits at L12–14. Negative control only lives in dead fallback unless import fails. |
| C14 | FE poll interval 2–5 s (`?pollMs=`) | **FAIL\*** | Source has `POLL_MS = Math.max(2000, Math.min(5000, …))` and `setInterval(pollPatch, POLL_MS)` — **unreachable** until C16 fixed |
| C15 | Hold / Manual freezes remote apply | **FAIL\*** | Source: `applyPatch` / `pollPatch` early-return when `holdManual`; button toggles — **unreachable** until C16 fixed |
| C16 | Frontend script parses (Hold/poll/telemetry live) | **FAIL** | `node --check` → `SyntaxError: Identifier 'telSensOrient' has already been declared` at duplicate `const` L494 and L497 |
| C17 | FE `clampPatch` windows ⊆ / align with contract | **FAIL** | FE: `pulseMs` 40–**220**, `shriekMs` 30–120, `vibThreshold` 0.02–0.8. Contract/BE: 20–**200**, 20–120, 0.01–2.0. FE **allows pulseMs>200** |

\*C14/C15 intent is present in source; runtime **FAIL** is driven by C16.

---

## Dry-run assert status (greens)

**Stale assert is already fixed** in current tree (`scripts/autoroute_dev.sh:61–68`). No RED edit applied.

If a branch still has the old block:

```bash
# BROKEN (old)
ok, msg, _ = validate_patch({"algo": "hop", "vol": 50, ...})
assert not ok, msg   # fails under vol_hard_max=100
```

**Exact greens fix** (already landed here):

```python
ok50, msg50, clamped50 = validate_patch({"algo": "hop", "vol": 50, "fMin": 17000, "fMax": 23000})
assert ok50 and clamped50.get("vol") == 50.0, (msg50, clamped50)
ok_lin, msg_lin, clamped_lin = validate_patch({"algo": "hop", "vol": 0.5, "fMin": 17000, "fMax": 23000})
assert ok_lin and clamped_lin.get("vol") == 50.0, (msg_lin, clamped_lin)
ok_hi, msg_hi, _ = validate_patch({"algo": "hop", "vol": 101, "fMin": 17000, "fMax": 23000})
assert not ok_hi, msg_hi
```

**Remaining greens work for C13:** either delete the early-exit preference and always run the assert block, or add the same `vol=101` refuse assert inside `iot_asp_autoroute/dry_run.py` so the default path covers the negative control.

---

## Frontend SyntaxError — exact greens fix (C16)

Delete the duplicate declaration at `public/index.html:497`:

```diff
  const telBand = $("telBand"), telLf = $("telLf"), telPower = $("telPower");
- const telSensOrient = $("telSensOrient"), telSensLight = $("telSensLight");
  const armSensorsBtn = $("armSensorsBtn");
```

Keep the first declaration at L494. Re-verify: `node --check` on extracted script → exit 0.

---

## FE clamp drift — exact greens fix (C17)

Align `clampPatch` (and local suddenFreq jitter at ~759–760) with backend/`api-contract.md`:

| Param | Change to |
|-------|-----------|
| `pulseMs` | `Math.max(20, Math.min(200, …))` |
| `shriekMs` | `Math.max(20, Math.min(120, …))` |
| `vibThreshold` | `Math.max(0.01, Math.min(2.0, …))` |

`vol` / `VOL_PATCH_MAX=100` already match.

---

## Commands run (evidence)

```text
bash scripts/autoroute_dev.sh          → exit 0, DRY-RUN OK
forced fallback heredoc                → exit 0, OK autoroute_dev dry-run
python validate_patch probes           → C1–C7 PASS
node --check (extracted IIFE)          → SyntaxError telSensOrient (C16 FAIL)
rg GEMINI|VERTEX|API_KEY public/       → no matches (C9)
```

No Vercel deploy performed.

---

## Summary for greens

1. **Backend clamps ↔ contract:** green (C1–C10).
2. **Dry-run happy path:** green; **fallback asserts:** green (fixed); **default-path refuse assert:** still missing (C13).
3. **Must-fix before promote:** remove duplicate `const` (C16) so Hold/poll actually run; align FE `clampPatch` to contract (C17).
