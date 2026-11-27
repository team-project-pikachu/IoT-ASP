# #26 closeout — Colab live GCS features (dry-run on main)

**Date:** 2026-10-12 (UTC)  
**Worker:** iot-asp-issue-queue-drain  
**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/26

## Status on main

Dry-run / offline path is on `main`:

- `services/autoroute-adk/iot_asp_autoroute/features_live.py` (sensor projection, json+jsonl read, `meta/features/` write guard, path-safety)
- `tests/test_features_live.py` (FL-01 … FL-16)
- `notebooks/iot_asp_colab_etl.md` + `.ipynb` (userdata names only)
- `.vv/colab-sensors.md` (offline PASS, live PENDING)
- `scripts/colab_live_gcs.sh` + `scripts/colab_gcs_fixture.sh` + golden fixture
- Spec: `docs/specs/26-colab-live-gcs-features.md`

Live GCS write remains **owner-gated**: requires Colab `userdata` named `GCP_SA_JSON`, `IOT_ASP_GCS_BUCKET`, `LIVE_GCS=1` (and corresponding GCP SA). No secret values, no live bucket URIs, no invented results in this evidence.

## Invariants preserved

- No breaking wire change; `schemaVersion` stays 1
- `vol_hard_max` = 100 (untouched)
- Hold / Manual freeze remote patch apply (untouched)
- No keys in `public/`
- Features never write `meta/patches/`

## Residual

Owner runs the notebook or CLI with live env names only and records a redacted `gs://…/meta/features/…` URI in `.vv/colab-sensors.md`. Until then the issue stays open for the live slice.

## Related

Parent #17. Prior Balanced PR3 fixture coverage already on main.
