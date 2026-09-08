# RED quick re-verify — post F1 fix

| Field | Value |
|-------|--------|
| **Reverify UTC** | `2026-09-08T00:20:07Z` |
| **Revision** | `fb73e6df56d84359bab65d452c33fd1f225c7de1` (`fb73e6d`) |
| **Repo** | `/Users/machine/apps/IoT-ASP` |
| **Scope** | F1 / C16 duplicate `telSensOrient`; C17 FE `clampPatch` `pulseMs≤200`; dry-run exit |
| **Deploy** | **not** run |
| **Plan** | **not** edited |
| **Verdict** | **PASS** |

---

## Checks

| ID | Check | Result | Evidence |
|----|-------|--------|----------|
| R1 | No duplicate `const telSensOrient` | **PASS** | `rg -c 'const telSensOrient' public/index.html` → **1** (L494 only) |
| R2 | Extracted IIFE parses | **PASS** | `node --check` on extracted inline script → exit **0** |
| R3 | FE `clampPatch` `pulseMs` ≤ 200 | **PASS** | `public/index.html:1677` → `Math.max(20, Math.min(200, +out.pulseMs))`; no residual `min(220)` / `max(40,…)` on pulse |
| R4 | Offline dry-run | **PASS** | `bash scripts/autoroute_dev.sh` → `DRY-RUN OK`, exit **0**; clamp negatives + holdManual negatives OK |

---

## Notes

- Related FE clamps also aligned at reverify: `shriekMs` 20–120, `vibThreshold` 0.01–2.0 (`clampPatch` L1678–1679).
- This reverify covers the F1/C16/C17 dry-run slice only. Broader FAIL items (F3–F7 etc.) are unchanged; see [FAIL.md](FAIL.md) / [PASS.md](PASS.md).
- Do not promote to Vercel until browser Hold/poll smoke is accepted separately.
