# Vendored for ADK packaging.

Canonical source: `packages/algo-timestore/algo_timestore/`

- Sync: `bash scripts/sync_algo_timestore_to_adk.sh`
- Verify: `bash scripts/sync_algo_timestore_to_adk.sh --check`

`adk deploy … iot_asp_autoroute` only ships this agent package; the monorepo
`packages/` tree is not included.
