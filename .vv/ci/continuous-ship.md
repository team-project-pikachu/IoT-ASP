# Continuous-ship evidence — Deploy: dev → test → prod (issue #27)

**Config item:** `.github/workflows/deploy.yml` + `vercel.json` (`git.deploymentEnabled.main: false`) +
`scripts/deploy_smoke.sh` + `scripts/vercel_secrets_check.sh` + `tests/test_deploy_workflow.py`
**Docs:** `docs/deploy.md`, `docs/specs/27-continuous-ship-dev-test-prod.md`
**Date:** 2026-09-08 (UTC)
**Status:** `secrets not set as of 2026-09-08 (issue #27)` — no live Actions deploy run exists yet;
`deploy.yml` only fires from the default branch after merge, and the deploy jobs skip until the secrets below
are set. Everything offline is green (see Observed).

## What exists

| Item | Where |
|------|-------|
| Workflow `Deploy — dev → test → prod`; triggers `workflow_run` of `CI — no breaking changes` (main, success) + `workflow_dispatch` (`target` dev/test/prod, `ref`) | `.github/workflows/deploy.yml` |
| Jobs `secrets_check` → `gates` → `deploy_dev` (env `dev`) → `test` (env `test`) → `deploy_prod` (env `production`) | `.github/workflows/deploy.yml` |
| Vercel CLI pinned `vercel@59`; `vercel pull --yes --environment=…`, `vercel build`, `vercel deploy --prebuilt [--prod]` | `.github/workflows/deploy.yml` |
| Deploy-hook fallback (**`workflow_dispatch` only**; `curl -fsS -X POST`, prints job id + state only, polls ≤ 5 min until prod serves this checkout — `SMOKE_PUBLIC_DIR=public` build identity) | `.github/workflows/deploy.yml` `deploy_prod` |
| Build identity: served `ETag == md5/sha1(local file)` for `/`, `/patch.json`, `/manifest.webmanifest` (`SMOKE_PUBLIC_DIR`); no redirects (`--max-redirs 0`); bypass secret only over https/loopback | `scripts/deploy_smoke.sh` |
| Vercel Git auto-deploy for `main` disabled; all original headers preserved | `vercel.json` |
| Remote smoke: 200, `Hold / Manual` + `holdManual`, `Permissions-Policy` ∋ microphone, `patch.json` `schemaVersion == 1`, manifest `Content-Type` | `scripts/deploy_smoke.sh` |
| Local secret-name pre-flight + 1Password / `gh secret set` recipe | `scripts/vercel_secrets_check.sh` |

## Required secret NAMES (values never recorded here)

| Name | Purpose | Set? |
|------|---------|------|
| `VERCEL_TOKEN` | Vercel CLI auth (team-scoped token) | no (2026-09-08) |
| `VERCEL_ORG_ID` | `.vercel/project.json` `orgId` (`<team_… placeholder>`) | no (2026-09-08) |
| `VERCEL_PROJECT_ID` | `.vercel/project.json` `projectId` (`<prj_… placeholder>`) | no (2026-09-08) |
| `VERCEL_DEPLOY_HOOK_PROD` | Deploy Hook `gh-actions-prod` URL (fallback path) | no (2026-09-08) |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | optional; preview Deployment Protection bypass | no (2026-09-08) |
| repo variable `PROD_URL` | optional; defaults to `https://hop-ultrasonic-1digital-design.vercel.app` | not set (default used) |

## Requirements

| ID | Requirement |
|----|-------------|
| DP-01 … DP-13 | Acceptance table in `docs/specs/27-continuous-ship-dev-test-prod.md` (workflow parse/name, triggers, permissions + concurrency, job graph, environments, success guard, CLI flags, secrets hygiene, `secrets_check` contract, smoke script offline behaviour, `vercel.json`, docs + evidence, dispatch semantics) |
| DP-14 … DP-17 | Adversarial-review regressions (2026-09-08): missing-header diagnostic under `pipefail`; redirect never followed / bypass secret never forwarded off-host or over plaintext; build identity via ETag; hook path dispatch-only with identity-checked poll |

## Procedure

```bash
python3 -m pytest tests/test_deploy_workflow.py -q
bash -n scripts/deploy_smoke.sh scripts/vercel_secrets_check.sh
bash scripts/deploy_smoke.sh                                   # usage → exit 2
SMOKE_RETRIES=1 SMOKE_SLEEP_S=0 bash scripts/deploy_smoke.sh http://127.0.0.1:9   # closed port → FAIL, exit 1
bash scripts/deploy_smoke.sh https://hop-ultrasonic-1digital-design.vercel.app    # network
SMOKE_RETRIES=1 SMOKE_SLEEP_S=0 SMOKE_PUBLIC_DIR=public bash scripts/deploy_smoke.sh https://hop-ultrasonic-1digital-design.vercel.app   # network; identity vs this checkout
bash scripts/vercel_secrets_check.sh                           # names only
bash scripts/ci_static_gates.sh
bash scripts/autoroute_dev.sh
python3 -m pytest tests -q
```

## Observed (local, 2026-09-08, Python 3.11 / PyYAML 6.0.1)

| Check | Result |
|-------|--------|
| `python3 -m pytest tests/test_deploy_workflow.py -q` | exit 0 — 18 passed (DP-01 … DP-17 + secrets-check script; DP-14/15/16 run loopback HTTP servers on 127.0.0.1, no outbound network) |
| `bash -n` both scripts | exit 0 |
| `bash scripts/deploy_smoke.sh` (no args) | exit 2 — `usage: scripts/deploy_smoke.sh <url> …` |
| `SMOKE_RETRIES=1 SMOKE_SLEEP_S=0 bash scripts/deploy_smoke.sh http://127.0.0.1:9` | exit 1 — `retry 1/1 … HTTP 000`, `FAIL: GET http://127.0.0.1:9 -> HTTP 000 (expected 200)` |
| `bash scripts/deploy_smoke.sh https://hop-ultrasonic-1digital-design.vercel.app` | exit 0 — `ok:` ×5, `OK deploy_smoke https://hop-ultrasonic-1digital-design.vercel.app` (currently served build already satisfies the smoke contract — which is exactly why plain smoke is not a ship signal) |
| `SMOKE_RETRIES=1 SMOKE_SLEEP_S=0 SMOKE_PUBLIC_DIR=public bash scripts/deploy_smoke.sh https://hop-ultrasonic-1digital-design.vercel.app` | exit 1 — `identity: / ETag '0c9f…787b' != local md5 7575…3b78 … served build is not this checkout (yet)`, `FAIL: GET … -> HTTP 200 but build identity mismatch (expected 200)`. Expected: prod predates this checkout (`/patch.json` and `/manifest.webmanifest` ETags **do** equal the local md5 — confirms the ETag == md5 scheme) |
| `curl -sS -D - -o /dev/null …/patch.json` vs `md5sum public/patch.json` | `etag: "5e3a654b5d44fb82a9295869b96a835f"` == local md5 (2026-09-08); same for `/manifest.webmanifest` |
| `bash scripts/vercel_secrets_check.sh` (clean shell) | exit 1 — `VERCEL_TOKEN: MISSING`, `VERCEL_ORG_ID: MISSING`, `VERCEL_PROJECT_ID: MISSING`, recipe printed, no values |
| same with the three names exported to dummy values | exit 0 — `OK vercel_secrets_check`; dummy values not echoed |
| `yaml.safe_load(deploy.yml)` job order | `secrets_check, gates, deploy_dev, test, deploy_prod` |
| `bash scripts/ci_static_gates.sh` | exit 0 — `OK ci_static_gates` |
| `bash scripts/autoroute_dev.sh` | exit 0 — dry-run OK |

## Remote Actions

| Run | SHA | Result |
|-----|-----|--------|
| — | — | none yet: `secrets not set as of 2026-09-08 (issue #27)`; first `workflow_run` fires after merge to `main`. Expected until then: `secrets_check` prints `::notice title=Vercel secrets::missing: VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID VERCEL_DEPLOY_HOOK_PROD — see docs/deploy.md and issue #27`, `gates` green, `deploy_dev` / `test` / `deploy_prod` skipped. |

## Pass/fail

| Req | Status |
|-----|--------|
| DP-01 … DP-17 (offline) | **PASS** (local) |
| Review findings (header diagnostic, redirect/bypass leak, hook false-green) | **FIXED** — regression tests DP-14 … DP-17 |
| Live dev → test → prod run | **PENDING** — blocked on secrets (owner action, `docs/deploy.md` §b–d) |

## Trigger-SHA invariant

Every checkout in `gates`, `deploy_dev`, `test`, and `deploy_prod` uses
the run-level `DEPLOY_REF`. A `workflow_run` computes it from
`github.event.workflow_run.head_sha`, so all gates and deployments use
the exact commit CI tested. A manual dispatch uses its requested `ref`,
or `main` when that input is empty.
