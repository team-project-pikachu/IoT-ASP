# CI — no breaking changes (issue-linked PRs)

GitHub Actions workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

## When it runs

| Event | Branches | Notes |
|-------|----------|--------|
| `pull_request` (`opened` / `synchronize` / `reopened`) | `main` | Full gates + **issue reference** check |
| `push` | `main` | Full gates (no PR-body issue check) |

Issue-linked PRs are the intended path for Project 5 Todo work (#12, #16, #17, research #9, design #13). Use the [PR template](../.github/PULL_REQUEST_TEMPLATE.md) with `Fixes #N` / `Closes #N` / `Related: #N`.

## Jobs

1. **`autoroute`** — asserts `vol_hard_max == 100` first (legacy “hard max 20” drift), installs `services/autoroute-adk/requirements.txt`, runs `bash scripts/autoroute_dev.sh`, timestore sim, **vendor sync `--check`**, **ADK-only layout import smoke** (`scripts/adk_layout_import_smoke.sh`), then import smoke for clamps / sudden_freq / Hold refuse.
2. **`static_gates`** — `bash scripts/ci_static_gates.sh`: Hold/Manual in `public/index.html`, no obvious API-key patterns in HTML, `public/patch.json` `schemaVersion: 1`, clamp constants.
3. **`pr_issue_ref`** (PR only) — fails if title/body lack an issue ref (`#N` or `Fixes`/`Closes`/`Resolves`/`Related` `#N`).
4. **`tests`** — `pip install -r requirements-dev.txt` then `python -m pytest tests -q` (converter, fleet log, micDiff, live features, ruleset JSON, deploy workflow, public HTML).
5. **`mdc check`** — `python3 scripts/mdc_convert.py --check` (Cursor `.mdc` → Claude Code outputs are fresh).
6. **`e2e smoke`** — Playwright against `public/` (`tests/e2e/run.sh`); informative, not required by the ruleset.

## Continuous ship

After green CI for a push to `main`, `deploy.yml` runs dev → test →
production. It re-runs static, autoroute, clamp, and pytest gates,
builds a Vercel preview, smoke-tests that exact preview, then promotes
production. Every checkout uses one `DEPLOY_REF`:
`workflow_run.head_sha` for CI-triggered runs, or the requested dispatch
ref (default `main`) for manual runs. Missing Vercel secrets produce a
notice and skip deployment; see [deploy.md](deploy.md) for setup,
fallback, rollback, and environment protection (issue #27).

## Vercel deploy notifications (webhooks)

Outbound Vercel **webhooks** (HMAC `x-vercel-signature`, secret name `VERCEL_WEBHOOK_SECRET`) are
documented in [vercel-webhooks.md](vercel-webhooks.md) (issue #37). Actions receives notifications via
`repository_dispatch` `vercel-deployment` (`.github/workflows/vercel-webhook.yml`) after an external
HTTPS receiver verifies the signature — complementary to Deploy Hooks / CLI ship in #27, not a
substitute. Settings UI:
<https://vercel.com/1digital-design/hop-ultrasonic/settings/webhooks>.

## Required on `main`

The five job `name:` values 1–5 above are the required status checks in the `main-protection` ruleset
(`.github/rulesets/main-protection.json`, applied with `make protect-main`). Renaming a job requires updating the
JSON in the same PR — `tests/test_ruleset_json.py` fails otherwise. See [branch-protection.md](branch-protection.md).

## Local reproduction

```bash
bash scripts/ci_static_gates.sh
bash scripts/autoroute_dev.sh
bash scripts/sync_algo_timestore_to_adk.sh --check
bash scripts/adk_layout_import_smoke.sh
python3 -m pytest tests/test_deploy_workflow.py tests/test_public_html.py -q
```

Evidence package: [`.vv/ci/`](../.vv/ci/).

## Closed-issue log (#68)

Optional workflow [`.github/workflows/mvp-closed-log.yml`](../.github/workflows/mvp-closed-log.yml) runs on
`issues: [closed]` (and `workflow_dispatch`) and appends a metadata row via
`scripts/mvp_closed_log_append.sh`. It requests `contents: write` + `pull-requests: write`.
Default path opens/updates PR branch `automation/mvp-closed-log` (works with empty
`bypass_actors`). Set repo variable `MVP_CLOSED_LOG_PUSH_MAIN=1` only when Actions
may push `main`. Soft-fails with a notice if push is blocked — then:

```bash
bash scripts/mvp_closed_log_append.sh <issue-number>
# or
bash scripts/mvp_closed_log_append.sh --backfill
```

## Out of scope

- Heavy Firecrawl / link crawls
- Live GCP / Vertex / Vercel deploy — the Vercel dev → test → prod ship lives in `.github/workflows/deploy.yml` (see [deploy.md](deploy.md), issue #27)
- Hosting the public HTTPS webhook receiver (stub only: `services/vercel-webhook-receiver/`, docs #37)
- Editing SEBoK plan files
- Subtree/submodule of private `IoT-ASP-study` into public `main` (PII) — see [STUDY_PRIVATE.md](STUDY_PRIVATE.md) / #67
