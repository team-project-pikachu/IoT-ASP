# Vercel deploy evidence — integrate-deploy-board

| Field | Value |
|-------|--------|
| **UTC (final prod)** | `2026-09-08T00:41:39Z` |
| **Repo (source)** | `/Users/machine/apps/IoT-ASP` → `public/` + `vercel.json` |
| **Deploy root** | `/Users/machine/apps/hop-ultrasonic` (linked project `hop-ultrasonic`) |
| **Sim** | `bash scripts/autoroute_dev.sh` → **DRY-RUN OK**; mirror whitelist `cry_mirror`/`siren_mirror`/`death_metal_mirror` validate_patch OK; extracted `node --check` exit 0; micDiff/Hold markers intact |
| **Tree shipped** | Extreme micDiff burst lane + **contour-mirrors** (`cry_mirror`, `siren_mirror`, `death_metal_mirror`) in extreme rotation + UI |
| **GCP org note** | Prefer `betty@bearresearch.io` for GCP/Gemini Enterprise (see `docs/gcp-recordings.md`) — not used for Vercel CLI |

## Environments (dev → test → prod)

| Stage | URL | HTTP | Notes |
|-------|-----|------|-------|
| **dev** (preview) | https://hop-ultrasonic-jsxmvabu2-1digital-design.vercel.app/ | **200** | Pre–hot-apply-complete preview |
| **test** (preview) | https://hop-ultrasonic-iqtm1wkr8-1digital-design.vercel.app/ | **200** | Pre–hot-apply-complete preview |
| **prod** (alias) | https://hop-ultrasonic.vercel.app/ | **200** | Live; hot-apply HTML + `patch.json` **no-store** |

### Production deployment (contour-mirrors + burst)

| Field | Value |
|-------|--------|
| **Immutable** | https://hop-ultrasonic-6niq6mmby-1digital-design.vercel.app |
| **Inspect** | https://vercel.com/1digital-design/hop-ultrasonic/DwDa1FWWR1gvhUWR6D89JHjxJ84G |
| **Alias** | https://hop-ultrasonic.vercel.app/ — HTTP **200**; HTML contains `cry_mirror` / `siren_mirror` / `death_metal_mirror` + `micDiffLf` / `holdManual` |

## Hot-apply redeploy notes

1. Earlier integrate `--prod` shipped F1 + partial hot-apply markers; **hot-apply lane DONE** evidence is `.vv/hot-apply.md`.
2. Final redeploy (this file’s UTC) synced IoT-ASP `public/` + `vercel.json` → hop-ultrasonic and promoted production.
3. `vercel.json`: catch-all no longer overrides `/patch.json` Cache-Control (specific `/patch.json` rule last; non-patch Cache-Control via negative-lookahead source). Edge alias briefly served stale headers (`age`/HIT) then settled on **no-store**.
4. Client still cache-busts with `_cb=` + `cache: "no-store"` regardless of CDN.

## Project 5 board

| Issue | Status |
|-------|--------|
| #9 | **Done** (research closeout) |
| #12 | **Done** |
| #13 | **Done** (design closeout) |
| #16 | **Done** |
| #17 | **Done** |

Backlog (#14/#15/#18/#19) and leftovers (#20–#23) left unchanged.

## Notes

- IoT-ASP has no separate `.vercel` link; public surface is the `hop-ultrasonic` Vercel project.
- Prior preview URLs remain valid historical evidence; **prod alias is the live surface**.
- **Continuous ship (Actions):** `.github/workflows/deploy.yml` — after green CI push to `main`, preview then prod when `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` are set. See `docs/ci.md` and `.vv/ci/continuous-ship.md`.


## Burst→shriek / micDiff (follow-on)

| Field | Value |
|-------|--------|
| **UTC** | `2026-09-08T00:37:52Z` |
| **Evidence** | `.vv/burst-shriek.md` |
| **Prod** | https://hop-ultrasonic.vercel.app/ |
| **Immutable** | https://hop-ultrasonic-1v9i9gmot-1digital-design.vercel.app |
| **Issue** | #25 (HW AEC/LF leftovers → Project 5) |
