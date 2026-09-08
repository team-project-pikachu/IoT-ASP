# ADK packaging — algo_timestore vendor

## Problem

`adk deploy … iot_asp_autoroute` ships only
`services/autoroute-adk/iot_asp_autoroute/`. The #30 adapter used
`Path(__file__).parents[3] / "packages/algo-timestore"` on `sys.path`, which
works in the monorepo checkout but fails in the ADK-only layout.

## Fix

| Piece | Role |
|-------|------|
| `iot_asp_autoroute/algo_timestore/` | Vendored library (relative import) |
| `packages/algo-timestore/` | Canonical source of truth |
| `scripts/sync_algo_timestore_to_adk.sh` | Sync + `--check` drift gate |
| `scripts/adk_layout_import_smoke.sh` | Temp-dir ADK-only PYTHONPATH import |

## Local evidence

```bash
bash scripts/sync_algo_timestore_to_adk.sh --check
bash scripts/adk_layout_import_smoke.sh
bash scripts/autoroute_dev.sh
```

Expected: `OK algo_timestore vendor in sync…`, `OK adk_layout_import_smoke`,
`OK autoroute_dev dry-run`.
