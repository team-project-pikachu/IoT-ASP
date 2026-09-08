# Evidence — engine hot-apply (no manual refresh)

**Date:** 2026-09-07  
**Subject:** `public/index.html` patch poll + apply (synced to `hop-ultrasonic/public/index.html`)  
**Requirement:** Engine/autoroute param changes apply live in-session; no F5 / pull-to-refresh.

## Observed design (code)

| Item | Value |
|------|--------|
| Default poll | `BACKEND_POLL_MS_DEFAULT = 3000` |
| Clamp | `Math.max(2000, Math.min(5000, ?pollMs))` |
| Schedule | `setInterval(pollPatch, POLL_MS)` + first fire at 500 ms |
| Stop on error? | **No** — catch → `patchStatus = "offline"`; interval continues |
| Reload on patch? | **No** — `applyPatch` mutates live UI/Web Audio state only |
| Cache | `fetch(..., { cache: "no-store" })` + `_cb=<Date.now()>` on URL |
| CDN | `vercel.json` → `/patch.json` → `Cache-Control: no-store, no-cache, must-revalidate` |
| Service worker | None in repo |
| Dedup | `patchFingerprint` on algo/band/fMin/fMax/vol/pulseMs/shriekMs/vibThreshold/seedAction → status `current` if unchanged |

## Distinction

- **Hot-apply:** patch JSON / GCS live patch URL / Gemini autoroute writes.  
- **One reload after HTML deploy:** new `index.html` shell only.

## Docs

- `docs/api-contract.md` — Hot-apply vs HTML deploy  
- `docs/sdd-app-control.md` — same distinction in SDD loop  

## Verify (manual / CI-friendly)

1. Open app; note monitor line `poll Nms (hot-apply)`.  
2. Change `public/patch.json` (or live `?patch=` target) algo/vol without touching HTML.  
3. Within ≤5 s, monitor shows `patch applied…`; UI algo/vol update; **no** full document reload.  
4. With **Hold / Manual** on, status stays `held` and params do not change.  
5. HTML-only deploy still requires one navigation (out of scope for hot-apply).
