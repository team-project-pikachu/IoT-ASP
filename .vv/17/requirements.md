# Issue #17 — Requirements capture (SEBoK)

**CI:** IoT-ASP Colab + Gemini Enterprise pipeline  
**Source:** [GitHub #17](https://github.com/team-project-pikachu/IoT-ASP/issues/17), `docs/api-contract.md`, `docs/DESIGN_CONSTRAINTS.md`, plan lane `exec-17-colab`  
**Revision:** see `REVISION.txt`

| Req ID | Statement | Trace |
|--------|-----------|--------|
| R17-1 | Document Colab ↔ GCS ↔ Gemini Enterprise ↔ ADK flow | `docs/colab-gemini-pipeline.md` |
| R17-2 | Public starter notebook under `notebooks/` with no site PII | `notebooks/iot_asp_colab_etl.ipynb` |
| R17-3 | Feature extracts: spectra/vib + NS/seismo priors as labels (not CFD) | `colab_etl.extract_features` / `prior_hint` |
| R17-4 | Credential **refs** only; Colab userdata for `GCP_SA_JSON` | docs + notebook gated `LIVE_GCS` |
| R17-5 | SciPy anomaly path shared with ADK (1 Hz, vib quantum 0.0005 g) | `vib_anomaly.py` + notebook import |
| R17-6 | Feature columns match telemetry api-contract `schemaVersion: 1` | `TELEMETRY_FEATURE_COLUMNS` |
| R17-7 | Patch outputs from Colab are suggestions only; ADK clamps write | `suggest_patch_stub` |
| R17-8 | Hold/Manual refuses patch suggestion | negative control in dry-run |

**Out of scope this wave:** Vercel e2e, Project board → Done (integrate lane), live Gemini seat calls from every tab.
