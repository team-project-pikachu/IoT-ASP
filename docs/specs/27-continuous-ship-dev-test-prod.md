# #27 — Continuous ship: GitHub Actions dev → test → prod into Vercel (CLI + deploy hooks)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/27 (milestone M5)
Owned files: `.github/workflows/deploy.yml`, `vercel.json`, `docs/deploy.md`, `scripts/deploy_smoke.sh`,
`scripts/vercel_secrets_check.sh`, `tests/test_deploy_workflow.py`, `.vv/ci/continuous-ship.md`,
`.vv/deploy/VERCEL.md`, this spec.

## Status

**Spec written 2026-09-08 — code not yet on `main`.** Everything that can run offline (workflow structure
test, `vercel.json` header preservation, smoke-script argument handling) is a CI gate. The live path is
gated behind GitHub Actions secrets that are **not set as of 2026-09-08** (`VERCEL_TOKEN`,
`VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, optional `VERCEL_DEPLOY_HOOK_PROD`,
`VERCEL_AUTOMATION_BYPASS_SECRET`); until an owner sets them, `deploy.yml` runs `gates` and prints a
`::notice`, and the deploy jobs skip. Recorded as `secrets not set as of 2026-09-08 (issue #27)` in
`.vv/ci/continuous-ship.md` and `.vv/deploy/VERCEL.md`.

## Goal

GitHub Actions — not Vercel's Git integration — owns every deploy of `public/`. After the existing
`CI — no breaking changes` workflow succeeds on `main`, a second workflow re-runs the repo gates, ships a
**dev** preview with the Vercel CLI (`vercel pull` → `vercel build` → `vercel deploy --prebuilt`), smoke-tests
that preview URL (**test**), then ships **prod** (`vercel deploy --prebuilt --prod`, or — fallback when only
the deploy-hook secret exists — a `POST` to the `gh-actions-prod` Deploy Hook) and smoke-tests the production
URL. Missing secrets skip with a `::notice`; they never fail a run. Vercel's automatic deploy on push to
`main` is turned off in `vercel.json` (`git.deploymentEnabled.main: false`) so a commit produces exactly one
deploy, gated by Actions. Backend (ADK/Cloud Run) deploys stay independent (CLAUDE.md invariant 11).

```text
push/merge to main
   │
   ▼
CI — no breaking changes  (ci.yml: autoroute · static_gates · pr_issue_ref)
   │ workflow_run: completed && conclusion == success && head_branch == main
   ▼
Deploy — dev → test → prod  (deploy.yml, concurrency group deploy-main)
   ├─ secrets_check ── outputs has_cli / has_hook (names only, never values)
   ├─ gates ────────── ci_static_gates.sh · autoroute_dev.sh · pytest tests -q
   ├─ deploy_dev ───── env dev: vercel pull --environment=preview → build → deploy --prebuilt → preview_url
   ├─ test ─────────── env test: scripts/deploy_smoke.sh <preview_url>  [x-vercel-protection-bypass]
   └─ deploy_prod ──── env production: CLI (--prod) │ Deploy Hook gh-actions-prod → poll → smoke <PROD_URL>
```

## Shipped on `main`

Verified by reading the code at branch head `0625e91` (`git log --oneline -3`):

| What | Where |
|------|-------|
| Upstream workflow name `CI — no breaking changes` (em dash) — the exact string `workflow_run.workflows` must match | `.github/workflows/ci.yml:1` |
| `ci.yml` triggers: `push` to `main`, `pull_request` to `main`; concurrency `ci-${{ github.workflow }}-${{ github.ref }}` cancel-in-progress; `permissions: contents: read, pull-requests: read` | `.github/workflows/ci.yml:3-16` |
| `ci.yml` jobs are only `autoroute`, `static_gates`, `pr_issue_ref` — **no** `tests` job, so `deploy.yml` `gates` must run pytest itself | `.github/workflows/ci.yml:19`, `:83`, `:96` |
| `actions/checkout@v4`, `actions/setup-python@v5` with `python-version: "3.12"` (pins reused by `deploy.yml`) | `.github/workflows/ci.yml:23-27` |
| `vercel.json`: `cleanUrls`, `trailingSlash`, two `headers` rules (4 global headers incl. `Permissions-Policy: microphone=(self), …`, and `Content-Type: application/manifest+json` for `/manifest.webmanifest`); **no** `git` key yet | `vercel.json:1-21` (`Permissions-Policy` at `:8`, manifest rule at `:14-19`) |
| Smoke markers: `Hold / Manual` label + `id="holdPatchBtn"` | `public/index.html:326` |
| `holdManual` wire key and `SCHEMA_VERSION = 1` | `public/index.html:492`, `:435` |
| `<link rel="manifest" href="/manifest.webmanifest">` | `public/index.html:14` |
| `public/patch.json` `"schemaVersion": 1` | `public/patch.json:2` |
| Script conventions: `#!/usr/bin/env bash`, `set -euo pipefail`, `ROOT` from own path, `echo "OK ci_static_gates"` | `scripts/ci_static_gates.sh:1-5`, `:73`; `scripts/autoroute_dev.sh:1-4` |
| Static gate greps `Hold / Manual` / `holdManual` / `holdPatchBtn` (the same markers the smoke test asserts remotely) | `scripts/ci_static_gates.sh:16-18` |
| Test/tooling deps for the `gates` job: `pytest`, `numpy`, `scipy`, `PyYAML>=6,<7` | `requirements-dev.txt:2-5` |
| Evidence-package layout (`Config item`, `Date`, requirements table, `Procedure`, `Observed`) to mirror in `.vv/ci/continuous-ship.md` | `.vv/ci/EVIDENCE.md:1-30`, `.vv/ci/README.md` |
| Prod URL default `https://hop-ultrasonic-1digital-design.vercel.app` | `CLAUDE.md:7`, `README.md:7` |
| Rule text already describing `deploy.yml` (gates → dev → test → prod, secret names, `::notice`, pinned CLI major) | `.claude/rules/ci-and-workflows.md:11-13` |

Not on `main`: no `.github/workflows/deploy.yml`, no `docs/deploy.md`, no `scripts/deploy_smoke.sh`,
no `scripts/vercel_secrets_check.sh`, no `tests/test_deploy_workflow.py` (`tests/` holds only
`test_mdc_convert.py`), no `.vv/deploy/`, and `vercel.json` has no `git` block.

## Remaining scope

### `.github/workflows/deploy.yml` (new)

```yaml
name: Deploy — dev → test → prod
on:
  workflow_run:
    workflows: ["CI — no breaking changes"]
    types: [completed]
    branches: [main]
  workflow_dispatch:
    inputs:
      target: { description: "Stop after", type: choice, options: [dev, test, prod], default: prod }
      ref:    { description: "Git ref to deploy (default: main)", type: string, required: false }
permissions: { contents: read, deployments: write }
concurrency: { group: deploy-main, cancel-in-progress: false }
```

Top-level `env` (values are expressions, never literals):
`PROD_URL: ${{ vars.PROD_URL || 'https://hop-ultrasonic-1digital-design.vercel.app' }}`,
`TARGET: ${{ github.event.inputs.target || 'prod' }}` (a `workflow_run` event has no inputs → `prod`),
`DEPLOY_REF: ${{ github.event.inputs.ref || github.event.workflow_run.head_sha || github.sha }}`.

Every job that checks out uses `actions/checkout@v4` with `ref: ${{ env.DEPLOY_REF }}` so a `workflow_run`
deploys the commit CI actually tested (`workflow_run` runs the workflow file from the default branch and
checks out the default branch by default — source: GitHub docs *Events that trigger workflows*).

Run-level guard, applied to **every** job via `if:` (jobs, not the workflow, carry conditions):
`github.event_name == 'workflow_dispatch' || (github.event.workflow_run.conclusion == 'success' && github.event.workflow_run.head_branch == 'main')`.

| Job | `needs` | `if` (in addition to the run-level guard) | `environment` | Steps |
|-----|---------|------------------------------------------|---------------|-------|
| `secrets_check` | — | — | — | One step, `id: probe`, `env: { VT: ${{ secrets.VERCEL_TOKEN }}, VO: ${{ secrets.VERCEL_ORG_ID }}, VP: ${{ secrets.VERCEL_PROJECT_ID }}, HP: ${{ secrets.VERCEL_DEPLOY_HOOK_PROD }} }`. Bash: `has_cli=true` iff `-n "$VT" && -n "$VO" && -n "$VP"`, `has_hook=true` iff `-n "$HP"`; writes `has_cli=<bool>` and `has_hook=<bool>` to `$GITHUB_OUTPUT`; builds a `missing` list of **names** (`VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID VERCEL_DEPLOY_HOOK_PROD`) and prints `::notice title=Vercel secrets::missing: <names> — see docs/deploy.md and issue #27` when non-empty; always `exit 0`. Job `outputs: { has_cli: …, has_hook: … }`. Never `echo` a value. |
| `gates` | — | — | — | checkout · `actions/setup-python@v5` `3.12` (pip cache on `requirements-dev.txt` + `services/autoroute-adk/requirements.txt`) · `pip install -r requirements-dev.txt -r services/autoroute-adk/requirements.txt` · `bash scripts/ci_static_gates.sh` · `bash scripts/autoroute_dev.sh` · `python3 -m pytest tests -q` |
| `deploy_dev` | `[secrets_check, gates]` | `needs.secrets_check.outputs.has_cli == 'true'` | `name: dev`, `url: ${{ steps.deploy.outputs.preview_url }}` | checkout · `actions/setup-node@v4` `node-version: 20` · `npm i -g vercel@59` · env `VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}`, `VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}` on the job · `vercel pull --yes --environment=preview --token=${{ secrets.VERCEL_TOKEN }}` · `vercel build --token=${{ secrets.VERCEL_TOKEN }}` · step `id: deploy`: `url=$(vercel deploy --prebuilt --token=${{ secrets.VERCEL_TOKEN }})`; `echo "preview_url=$url" >> "$GITHUB_OUTPUT"`; `echo "dev preview: $url" >> "$GITHUB_STEP_SUMMARY"`. Job `outputs.preview_url`. |
| `test` | `[deploy_dev]` | `env.TARGET != 'dev'` (i.e. `test` or `prod`) | `name: test`, `url: ${{ needs.deploy_dev.outputs.preview_url }}` | checkout · `bash scripts/deploy_smoke.sh "${{ needs.deploy_dev.outputs.preview_url }}"` with `env: { BYPASS: ${{ secrets.VERCEL_AUTOMATION_BYPASS_SECRET }} }` (empty when unset; the script only sends `x-vercel-protection-bypass` when non-empty) |
| `deploy_prod` | `[secrets_check, gates, test]` | `!cancelled() && env.TARGET == 'prod' && needs.gates.result == 'success' && (needs.test.result == 'success' \|\| (needs.test.result == 'skipped' && needs.secrets_check.outputs.has_cli != 'true')) && (needs.secrets_check.outputs.has_cli == 'true' \|\| needs.secrets_check.outputs.has_hook == 'true')` | `name: production`, `url: ${{ env.PROD_URL }}` | checkout · setup-node 20 · `npm i -g vercel@59` · **CLI path** (`if: needs.secrets_check.outputs.has_cli == 'true'`): `vercel pull --yes --environment=production --token=…` · `vercel build --prod --token=…` · `url=$(vercel deploy --prebuilt --prod --token=…)`; `echo "prod_url=$url" >> $GITHUB_OUTPUT`; summary line · **Hook path** (`if: needs.secrets_check.outputs.has_cli != 'true' && needs.secrets_check.outputs.has_hook == 'true'`): `env: { VERCEL_DEPLOY_HOOK_PROD: ${{ secrets.VERCEL_DEPLOY_HOOK_PROD }} }`; `resp=$(curl -fsS -X POST "$VERCEL_DEPLOY_HOOK_PROD")`; `python3 -c 'import json,sys; j=json.load(sys.stdin)["job"]; print("deploy hook job", j["id"], j["state"])'` (prints **only** id + state; expects `{"job":{"id":…,"state":"PENDING",…}}`); then poll: up to **10 × 30 s (5 min)** running `bash scripts/deploy_smoke.sh "$PROD_URL"` until it exits 0 (`SMOKE_RETRIES=1` per attempt so the outer loop controls timing) · **Final smoke** (both paths): `bash scripts/deploy_smoke.sh "$PROD_URL"` with `BYPASS` env · append `prod: $PROD_URL` to `$GITHUB_STEP_SUMMARY`. |

Dispatch semantics (`env.TARGET`): `dev` → `secrets_check`, `gates`, `deploy_dev` only (`test` and
`deploy_prod` skip); `test` → through `test`; `prod` (default, and every `workflow_run`) → all five.
`deploy_prod` **must** list `secrets_check` and `gates` in `needs` because a job may only read
`needs.<job>.outputs` of jobs it depends on; `needs.test` is the ordering edge the brief requires.

Secret hygiene: every secret appears only as `${{ secrets.NAME }}` (job/step `env` or `--token=` argument
on a `run:` line); no `echo` of `$VT`/`$VERCEL_TOKEN`/hook URL; the deploy-hook URL is itself a secret
(it embeds the project id + hook key, Vercel docs *Deploy Hooks*). `vercel …` commands are the only
network calls besides `curl`; nothing in `deploy.yml` touches GCP.

### `vercel.json` (edit — additive only)

Add exactly one top-level key, keep every existing key/header byte-for-byte:

```json
"git": { "deploymentEnabled": { "main": false } }
```

Do **not** add `"github": { "enabled": false }` — that disables the GitHub integration entirely and Deploy
Hooks stop working (Vercel discussion #8619; brief). `git.deploymentEnabled` per-branch only suppresses
auto-deploy on push (Vercel docs *Git Configuration → git.deploymentEnabled*). Unlisted branches still
deploy automatically; that is intentional (PR previews from Vercel are harmless and cheap, and
`ci.yml`/`deploy.yml` never rely on them).

### `scripts/deploy_smoke.sh <url>` (new)

`#!/usr/bin/env bash`, `set -euo pipefail`, `ROOT` from own path, usage error (exit 2) without `<url>`.
Env: `BYPASS` (optional; when non-empty every `curl` adds `-H "x-vercel-protection-bypass: $BYPASS"`),
`SMOKE_RETRIES` (default `5`), `SMOKE_SLEEP_S` (default `6`). Trailing `/` stripped from `<url>`.
A `fetch()` helper does `curl -sS -L --max-time 20 -D "$hdr" -o "$body" -w '%{http_code}'` with retry
`SMOKE_RETRIES`× / `SMOKE_SLEEP_S` s on curl failure or non-200. Asserts, in order, each printing `ok:` or
`FAIL:` (exit 1):

1. `GET <url>` → HTTP `200`.
2. Body contains `Hold / Manual` **and** `holdManual` (same markers as `scripts/ci_static_gates.sh:16-17`).
3. Response header `Permissions-Policy` (case-insensitive) contains `microphone`.
4. `GET <url>/patch.json` → 200 and `python3 -c 'import json,sys; assert json.load(open(sys.argv[1]))["schemaVersion"] == 1' "$body"`.
5. `GET <url>/manifest.webmanifest` → 200 and `Content-Type` starts with `application/manifest+json`.

Never prints `BYPASS`; on success prints `OK deploy_smoke <url>`. Temp files under `mktemp -d`, trapped.
Offline self-check: `bash scripts/deploy_smoke.sh` (no args) exits 2 and prints `usage:`; a URL to a closed
local port fails with `FAIL:` after the retries (used by DP-10 with `SMOKE_RETRIES=1 SMOKE_SLEEP_S=0`).

### `scripts/vercel_secrets_check.sh` (new, local use only)

`#!/usr/bin/env bash`, `set -euo pipefail`. For each of `VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID`
(+ optional `VERCEL_DEPLOY_HOOK_PROD`, `VERCEL_AUTOMATION_BYPASS_SECRET`) prints `NAME: set` / `NAME: MISSING`
using `${!name:+x}` only — never the value. Then prints the copy-paste recipe (static text):

```bash
# 1Password Environment "dev" (item names, not values)
op read "op://dev/VERCEL_TOKEN/credential"
op read "op://dev/VERCEL_ORG_ID/credential"
op read "op://dev/VERCEL_PROJECT_ID/credential"
op read "op://dev/VERCEL_DEPLOY_HOOK_PROD/credential"
# GitHub Actions secrets — value piped on stdin, never on the command line
op read "op://dev/VERCEL_TOKEN/credential"            | gh secret set VERCEL_TOKEN            --repo team-project-pikachu/IoT-ASP
op read "op://dev/VERCEL_ORG_ID/credential"           | gh secret set VERCEL_ORG_ID           --repo team-project-pikachu/IoT-ASP
op read "op://dev/VERCEL_PROJECT_ID/credential"       | gh secret set VERCEL_PROJECT_ID       --repo team-project-pikachu/IoT-ASP
op read "op://dev/VERCEL_DEPLOY_HOOK_PROD/credential" | gh secret set VERCEL_DEPLOY_HOOK_PROD --repo team-project-pikachu/IoT-ASP
```

Exit 0 when the three CLI names are set, 1 otherwise (so it can be used as a pre-flight). Prints
`OK vercel_secrets_check` on success.

### `docs/deploy.md` (new)

Sections, in order: (a) architecture diagram (the ASCII block above) + trigger table; (b) one-time Vercel
setup at `https://vercel.com/1digital-design/hop-ultrasonic/settings/git` — connect GitHub repo
`team-project-pikachu/IoT-ASP`, production branch `main`, automatic deploys for `main` stay off via
`vercel.json` `git.deploymentEnabled`, create Deploy Hook `gh-actions-prod` on ref `main` and store its URL
as GitHub secret `VERCEL_DEPLOY_HOOK_PROD` (hook URLs are secrets; never set `github.enabled: false`);
(c) token path — create a Vercel token scoped to team `1digital-design`, store in 1Password env `dev`,
`gh secret set` the three names + hook (the recipe above); org/project ids come from `vercel link` →
`.vercel/project.json` (`orgId`, `projectId`) — placeholders only in docs; (d) GitHub Environments `dev`,
`test`, `production` (Settings → Environments), optional required reviewers on `production` (up to 6,
one approval suffices); (e) running `workflow_dispatch` (`gh workflow run "Deploy — dev → test → prod" -f target=dev [-f ref=<sha>]`);
(f) rollback: `vercel rollback <url>` reverts production to a previous deployment; `vercel promote <url>`
moves an existing (verified) deployment to production without rebuilding — blue/green: `vercel --prod --skip-domain`
→ verify → `vercel promote`; (g) evidence expectations — every real run refreshes `.vv/ci/continuous-ship.md`
(run URL, job results, preview/prod URLs, exit codes; no secrets). Ends with a **Sources** list (see below).

### `tests/test_deploy_workflow.py` (new; PyYAML + stdlib, offline)

Loads `.github/workflows/deploy.yml` with `yaml.safe_load`; note PyYAML 1.1 parses the bare `on` key as
boolean `True`, so read `wf.get("on", wf.get(True))`. Also loads `vercel.json` with `json`. Tests are the
DP-* rows below.

### `.vv/ci/continuous-ship.md` + `.vv/deploy/VERCEL.md` (new)

Evidence format per `.vv/ci/EVIDENCE.md`: config item, UTC date, requirement table (DP-01…), procedure
(`python3 -m pytest tests/test_deploy_workflow.py -q`, `bash scripts/deploy_smoke.sh https://hop-ultrasonic-1digital-design.vercel.app`
when network is available, `bash scripts/vercel_secrets_check.sh`), observed results with exit codes, and
the status line `secrets not set as of 2026-09-08 (issue #27)`. `VERCEL.md` lists: what exists (project
`hop-ultrasonic`, team `1digital-design`, prod URL), required secret **names**, `VERCEL_ORG_ID: <team_… placeholder>`,
`VERCEL_PROJECT_ID: <prj_… placeholder>` (ids are **not** invented), Deploy Hook name `gh-actions-prod`
(URL is a secret), GitHub Environments to create, and `status: secrets not set as of 2026-09-08 (issue #27)`.

### Integration requests (not owned here)

- `docs/ci.md` "Out of scope" → add `Live Vercel deploy lives in deploy.yml (docs/deploy.md)`; README
  `## Deploy` link to `docs/deploy.md`. (`.claude/rules/ci-and-workflows.md:12` already describes
  `deploy.yml`; no change needed.)
- `ci.yml` is **not** modified; `deploy.yml` depends only on its `name:` string (`ci.yml:1`).

## Wire fields

None. `schemaVersion: 1` unchanged; the smoke test only *reads* `public/patch.json` `schemaVersion` and the
`holdManual` marker. No telemetry/patch field is added or renamed (`docs/api-contract.md` untouched).

## Clamps / safety

- **Secrets by name only**: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `VERCEL_DEPLOY_HOOK_PROD`,
  `VERCEL_AUTOMATION_BYPASS_SECRET` referenced solely as `${{ secrets.NAME }}`; `secrets_check` prints
  names of missing secrets, never values; `vercel_secrets_check.sh` tests presence with `${!name:+x}`.
  Repo variable `PROD_URL` is public config, not a secret.
- **Never fail on missing secrets**: `secrets_check` always exits 0; deploy jobs `if:`-skip.
- **Least privilege**: `permissions: contents: read, deployments: write`; no `id-token`, no `pull-requests`.
- **One deploy per commit**: `vercel.json` `git.deploymentEnabled.main: false` + concurrency
  `deploy-main` (no cancel-in-progress, so a prod deploy is never killed mid-flight).
- **Prod only after test**: `deploy_prod` requires `needs.gates.result == 'success'` and
  `needs.test.result == 'success'` on the CLI path; the hook-only path (no CLI secrets → `deploy_dev`/`test`
  skipped) still requires green `gates` and runs the smoke against prod after the hook.
- **`--prod` appears only in `deploy_prod`**; `--prebuilt` and `--yes` are mandatory (no interactive
  prompts, no double build — Vercel KB).
- **Frontend invariants hold remotely**: smoke asserts `Hold / Manual`, `holdManual`, `schemaVersion == 1`,
  `Permissions-Policy` contains `microphone`, manifest `Content-Type` — the same C1/Hold gates as
  `scripts/ci_static_gates.sh`, now against the served site. No Web Bluetooth, no keys, no PII touched.
- **Backend untouched**: `deploy.yml` never calls GCP/ADK; `services/autoroute-adk/` deploys independently.
- **CLI pin**: `vercel@59` (major of npm `latest` 59.11.7 on 2026-09-08, engines `node >= 18`);
  `actions/setup-node@v4` Node 20 (Vercel deprecates Node 20 *runtime* on 2026-10-01 — that is the
  serverless runtime, irrelevant to a static site; the CLI itself needs ≥ 18. Bump to 22/24 freely).

## Acceptance tests (`tests/test_deploy_workflow.py`, offline, deterministic)

| ID | Test | Check |
|----|------|-------|
| DP-01 | Workflow parses + name | `yaml.safe_load` succeeds; `wf["name"] == "Deploy — dev → test → prod"` |
| DP-02 | Triggers | `on.workflow_run.workflows == ["CI — no breaking changes"]` (equals line 1 of `ci.yml` read at test time), `types == ["completed"]`, `branches == ["main"]`; `on.workflow_dispatch.inputs.target.type == "choice"`, `options == ["dev","test","prod"]`, `default == "prod"`; `inputs.ref` present, not required |
| DP-03 | Permissions + concurrency | `permissions == {"contents":"read","deployments":"write"}`; `concurrency.group == "deploy-main"`; `concurrency["cancel-in-progress"] is False` |
| DP-04 | Job graph | jobs keys ⊇ `{secrets_check, gates, deploy_dev, test, deploy_prod}`; `set(deploy_dev.needs) == {"secrets_check","gates"}`; `test.needs == ["deploy_dev"]`; `"test" in deploy_prod.needs and "secrets_check" in deploy_prod.needs and "gates" in deploy_prod.needs`; `secrets_check` and `gates` have no `needs` |
| DP-05 | Environments | `deploy_dev.environment.name == "dev"`, `test.environment.name == "test"`, `deploy_prod.environment.name == "production"` and its `url` contains `PROD_URL` |
| DP-06 | Success guard | every job's `if` string contains `workflow_run.conclusion == 'success'` and `head_branch == 'main'`; `deploy_dev.if` contains `has_cli == 'true'`; `deploy_prod.if` contains `has_hook` and `!cancelled()` |
| DP-07 | CLI flags | concatenated `run:` text of `deploy_dev` contains `vercel pull --yes --environment=preview`, `vercel build`, `vercel deploy --prebuilt` and **not** `--prod`; `deploy_prod` contains `--environment=production`, `vercel build --prod`, `vercel deploy --prebuilt --prod`, `curl -fsS -X POST`, `scripts/deploy_smoke.sh`; `--prod` appears in no other job; both deploy jobs contain `npm i -g vercel@59` (regex `vercel@\d+`) |
| DP-08 | Secrets hygiene | raw file: every occurrence of `secrets.` matches `\$\{\{\s*secrets\.[A-Z_]+\s*\}\}`; set of names == `{VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID, VERCEL_DEPLOY_HOOK_PROD, VERCEL_AUTOMATION_BYPASS_SECRET}`; regex `AIza[0-9A-Za-z_-]{20,}\|vercel_[A-Za-z0-9]{10,}\|sk-[A-Za-z0-9]{20,}` has no match in `deploy.yml`, `vercel.json`, `docs/deploy.md`, both scripts, both `.vv` files; no `echo` line references `$VT`, `$VO`, `$VP`, `$HP`, `$VERCEL_TOKEN`, or `$VERCEL_DEPLOY_HOOK_PROD` |
| DP-09 | secrets_check contract | its single step's `env` keys == `{VT, VO, VP, HP}` mapped to the three CLI secrets + hook; `run` writes `has_cli=` and `has_hook=` to `$GITHUB_OUTPUT`, contains `::notice`, `docs/deploy.md`, `issue #27`; job `outputs` has `has_cli`, `has_hook`; no `exit 1` in the step |
| DP-10 | Smoke script | `subprocess.run(["bash","scripts/deploy_smoke.sh"])` → returncode 2, stderr contains `usage:`; with `SMOKE_RETRIES=1 SMOKE_SLEEP_S=0` against `http://127.0.0.1:9` → non-zero, output contains `FAIL:`; file text contains `Hold / Manual`, `holdManual`, `schemaVersion`, `Permissions-Policy`, `microphone`, `application/manifest+json`, `x-vercel-protection-bypass`, `OK deploy_smoke`; `bash -n` passes for both scripts |
| DP-11 | vercel.json | `cfg["git"]["deploymentEnabled"]["main"] is False`; `"github" not in cfg`; `cfg["cleanUrls"] is True`, `cfg["trailingSlash"] is False`; `cfg["headers"]` contains a `/(.*)` rule whose header keys == `{Permissions-Policy, Referrer-Policy, X-Content-Type-Options, Cache-Control}` with the exact original values (`microphone=(self), autoplay=(self), accelerometer=(self), gyroscope=(self)`, `strict-origin-when-cross-origin`, `nosniff`, `public, max-age=0, must-revalidate`) and a `/manifest.webmanifest` rule with `Content-Type: application/manifest+json` |
| DP-12 | Docs + evidence | `docs/deploy.md` contains `vercel.com/1digital-design/hop-ultrasonic/settings/git`, `gh-actions-prod`, `VERCEL_DEPLOY_HOOK_PROD`, `gh secret set`, `vercel rollback`, `vercel promote`, `## Sources`; `.vv/ci/continuous-ship.md` and `.vv/deploy/VERCEL.md` contain `secrets not set as of 2026-09-08 (issue #27)`; `scripts/vercel_secrets_check.sh` contains `op://dev/` and `gh secret set VERCEL_TOKEN --repo team-project-pikachu/IoT-ASP` |
| DP-13 | Dispatch semantics | `test.if` contains `TARGET != 'dev'`; `deploy_prod.if` contains `TARGET == 'prod'`; top-level `env.TARGET` expression contains `inputs.target` and `'prod'` fallback; `env.DEPLOY_REF` contains `workflow_run.head_sha` |

## CI gate

- `tests` in `deploy.yml`'s own `gates` job and (once the integrator adds a pytest job to `ci.yml`) in CI:
  `python3 -m pytest tests/test_deploy_workflow.py -q` — offline, no network (DP-10 hits a closed port only).
- `bash scripts/ci_static_gates.sh` unchanged and green (`vercel.json` is not on its path; `public/`
  untouched).
- `bash -n scripts/deploy_smoke.sh scripts/vercel_secrets_check.sh` (DP-10).
- Live deploy is **not** a CI gate (`docs/ci.md` "Out of scope"); evidence is `.vv/ci/continuous-ship.md`.
- `deploy.yml` only fires from the default branch (`workflow_run` semantics), so it cannot run on this
  feature branch; first real evidence arrives after merge + secrets.

## Risks / HW limits

- **`workflow_run` runs the workflow file from the default branch only** — edits to `deploy.yml` on a PR
  branch are inert until merged; test with `workflow_dispatch` `target=dev` after merge.
- **Vercel Deployment Protection**: if preview protection is enabled for the team, the `test` job fails
  with 401 unless `VERCEL_AUTOMATION_BYPASS_SECRET` is set (header `x-vercel-protection-bypass`).
- **Hook path cannot prove freshness**: the deploy-hook job id is not queryable without a token, so the
  poll only proves the prod URL serves a passing build, not that it is the *new* build. The CLI path is
  authoritative; the hook path is a fallback and is documented as such.
- **Hook fires a Vercel-side build of `main`** (Git integration), not the Actions checkout — so with a
  dispatch `ref` other than `main`, the hook path deploys `main` anyway; the workflow prints a `::warning`
  in that case.
- **Deploy Hooks require the GitHub integration** to stay connected; `github.enabled: false` would break
  them (Vercel discussion #8619) — hence `git.deploymentEnabled.main` instead.
- **Unlisted branches still auto-deploy on Vercel** (PR previews); harmless, but they bypass Actions.
  Extend to `"deploymentEnabled": false` only if the team wants Actions-only previews too.
- **`vercel deploy` prints the URL on stdout** (Context7 `/vercel/vercel` deployment reference); any extra
  stdout noise breaks `url=$(…)`. Keep `--token=` on the command (stderr carries progress).
- **Node deprecation**: Vercel deprecates Node 20 runtime on 2026-10-01 — irrelevant for `public/` (static),
  but bump `setup-node` to 22/24 at the next touch.
- Secrets are not set on 2026-09-08: until then every run ends at `gates` + `::notice`.

## Sources

- Context7 `/vercel/vercel` — `skills/vercel-cli/references/ci-automation.md` (standard CI pattern:
  `vercel pull --yes --environment=production` → `vercel build --prod` → `vercel deploy --prebuilt --prod`),
  `skills/vercel-cli/references/deployment.md` (`URL=$(vercel deploy --prod)` captures the URL on stdout;
  `vercel promote <url>`, `vercel rollback <url>`, blue/green `--skip-domain` → `promote`),
  `skills/vercel-cli/SKILL.md` (non-interactive flags, token via env not hard-coded),
  `packages/config/example/vercel.ts` (`git.deploymentEnabled: { <branch>: false }` per-branch object).
- Vercel KB — *How can I use GitHub Actions with Vercel?* https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel
  (`--prebuilt` avoids double builds; disable Git integration deploys via `vercel.json` `git.deploymentEnabled`).
- Vercel docs — *Deploying GitHub Projects with Vercel* https://vercel.com/docs/git/vercel-for-github
  (`npm install --global vercel@latest`, preview vs production `vercel pull --yes --environment=…`).
- Vercel docs — *Git Configuration* https://vercel.com/docs/project-configuration/git-configuration
  (`git.deploymentEnabled` branch map / globs / `false`).
- Vercel docs — *Creating & Triggering Deploy Hooks* https://vercel.com/docs/deploy-hooks
  (`curl -X POST <hook>` → `{"job":{"id":…,"state":"PENDING","createdAt":…}}`).
- GitHub discussion vercel/vercel #8619 https://github.com/vercel/vercel/discussions/8619
  (`github.enabled: false` stops Deploy Hooks from working).
- Vercel docs — *Protection Bypass for Automation*
  https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection/protection-bypass-automation
  (header/query `x-vercel-protection-bypass`, system env `VERCEL_AUTOMATION_BYPASS_SECRET`).
- npm registry `https://registry.npmjs.org/vercel/latest` queried 2026-09-08 → `59.11.7`, `engines.node >= 18`
  (pin `vercel@59`). Vercel changelog *Node.js 20 is being deprecated on October 1, 2026*
  https://vercel.com/changelog/node-js-20-is-being-deprecated
- GitHub docs — *Events that trigger workflows → `workflow_run`*
  https://docs.github.com/actions/using-workflows/events-that-trigger-workflows (default-branch-only,
  `github.event.workflow_run.conclusion`, `branches:` filter, `head_branch`).
- GitHub docs — *Workflow syntax → `on.workflow_dispatch.inputs`*
  https://docs.github.com/enterprise-cloud@latest/actions/reference/workflows-and-actions/workflow-syntax
  (`type: choice`, `options`, `default`; `github.event.inputs` empty for other events).
- GitHub docs — *Managing environments for deployment*
  https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment
  (required reviewers, up to 6, one approval suffices; environment `name`/`url`).
- Repo: `.github/workflows/ci.yml`, `vercel.json`, `scripts/ci_static_gates.sh`, `.vv/ci/EVIDENCE.md`,
  `.claude/rules/ci-and-workflows.md`, `.claude/rules/docs-and-specs.md`, GitHub issue #27.
