# ISSUE-26 — Colab live GCS features

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/26  
**Status:** dry-run + golden fixture (stack PR3); ETL dry-run + LIVE_GCS refuse tests (stack PR5); live PENDING

## Did

- `services/autoroute-adk/iot_asp_autoroute/features_live.py`
- `scripts/colab_live_gcs.sh` + `scripts/colab_gcs_fixture.sh` (`--check`)
- `scripts/colab_etl_dry_run.py` offline summary (asserted in pytest)
- `fixtures/colab_gcs/features_node1_seed26.json` golden
- `tests/test_colab_gcs_fixture.py` — shape, `--check`, ETL dry-run, refuse `LIVE_GCS=1`
- Notebooks / `.vv/colab-sensors.md` (names-only live gate)

## Didn't

- Invent `GCP_SA_JSON` / bucket values
- Run `LIVE_GCS=1`

## Next

- Owner Colab userdata run with `LIVE_GCS=1` when SA is in 1Password `dev`
