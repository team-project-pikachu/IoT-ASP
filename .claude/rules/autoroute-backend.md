---
paths:
  - "services/autoroute-adk/**"
  - "gcp/**"
  - "notebooks/**"
---

# Autoroute backend (`services/autoroute-adk/iot_asp_autoroute`)

- Package is importable without `google-adk` (`__init__.py` soft-fails `agent`). Keep every new module importable with stdlib + numpy/scipy only; guard optional imports.
- `clamps.validate_patch()` is the single source of truth for policy. New patch authors call it before any write; `tools.write_patch()` re-validates and refuses when the latest telemetry has `holdManual`.
- Constants that CI asserts: `SCHEMA_VERSION == 1`, `CLAMPS["vol_hard_max"] == CLAMPS["vol_soft_max"] == 100.0`, `ALLOWED_ALGOS` whitelist, `BAND_US = (17000, 23000)`, `BAND_LF = (10, 20)`.
- Storage goes through `gcs_io` only (dry-run mirror under `.autoroute-dry/` when `IOT_ASP_AUTOROUTE_DRY_RUN=1` or no bucket). Colab/ETL code writes `meta/features/` and `meta/logs/` — **never** `meta/patches/`.
- Priors (`priors.py`) are constraints for prompts; cite only IDs already in `reference/LITERATURE.md`. No CFD claims.
- Vib anomaly is authoritative in `vib_anomaly.py` (SciPy medfilt + MAD z-score, 1 Hz, 0.0005 g quantum). Reuse it; do not re-implement detection in notebooks.
- Timestamps UTC ISO-8601 `%Y-%m-%dT%H:%M:%SZ`; object names replace `:` with `-`.
- Every module gets a `tests/test_<module>.py` with negative controls (holdManual refuse, out-of-band refuse, nonsense keys ignored) and a `__main__`/CLI demo that runs offline.
- Secrets: env or Colab `userdata` **names** only (`GOOGLE_CLOUD_PROJECT`, `IOT_ASP_GCS_BUCKET`, `GCP_SA_JSON`). Never print or log values.
- ADK 2.x migration is parked (#24): keep `google-adk>=1,<2`, `google-genai>=1,<2` unless that issue is unparked.
