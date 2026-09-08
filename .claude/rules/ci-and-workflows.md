---
paths:
  - ".github/**"
  - "scripts/**"
  - "tests/**"
  - "Makefile"
---

# CI, workflows, scripts, tests

- `ci.yml` jobs: `autoroute` (drift gate `vol_hard_max=100` → `scripts/autoroute_dev.sh` → import smoke), `static_gates` (`scripts/ci_static_gates.sh`), `pr_issue_ref` (PR title/body must contain `#N`), plus `tests` (pytest) and `mdc_check`. Keep them fast and network-free; live GCP/Vertex/Vercel calls belong in `deploy.yml` only.
- `deploy.yml` is the continuous-ship pipeline: gates → **dev** (Vercel preview) → **test** (smoke against the preview URL) → **prod** (`vercel deploy --prebuilt --prod`). Secrets referenced by name only: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` (+ optional `VERCEL_AUTOMATION_BYPASS_SECRET`). When missing, jobs skip with a `::notice` pointing at `docs/deploy.md` and issue #27; they never fail the run.
- Vercel CLI in CI: pin the major, `vercel pull --yes --environment=<preview|production>`, `vercel build`, `vercel deploy --prebuilt [--prod]`, token via env/`--token`, never hard-coded (source: `/vercel/vercel` skills/vercel-cli references).
- Scripts are `#!/usr/bin/env bash` + `set -euo pipefail`, resolve `ROOT` from their own path, and print `OK <name>` on success. Python helpers are stdlib-first.
- Tests: pytest under `tests/`, offline, deterministic (seeded RNG, fixed timestamps, `tmp_path` for dry-run roots via `IOT_ASP_AUTOROUTE_DRY_ROOT`). Static HTML assertions in `tests/test_public_html.py`; workflow structure assertions in `tests/test_deploy_workflow.py`.
- Never skip, quarantine, or weaken a gate to get green. Fix the cause.
- `scripts/mdc_convert.py --check` must pass in CI; regenerate with `python3 scripts/mdc_convert.py` after editing `.cursor/rules/*.mdc`.
