# fixtures/colab_gcs — #26 dry-run golden

| File | Role |
|------|------|
| `features_node1_seed26.json` | Golden `meta/features` object from `--seed-demo` (seed=26, node1) |
| `run_live_seed_demo.json` | Scrubbed CLI summary (no host paths) |

Regenerate / verify:

```bash
bash scripts/colab_gcs_fixture.sh
bash scripts/colab_gcs_fixture.sh --check
```

Live GCS (`LIVE_GCS=1`, `IOT_ASP_GCS_BUCKET`, `GCP_SA_JSON`) is **owner-gated** — never committed.
