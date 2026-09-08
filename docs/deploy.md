# Deploy — continuous ship: GitHub Actions dev → test → prod into Vercel

Issue: [#27](https://github.com/team-project-pikachu/IoT-ASP/issues/27) · Spec:
[`docs/specs/27-continuous-ship-dev-test-prod.md`](specs/27-continuous-ship-dev-test-prod.md) ·
Workflow: [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) · Evidence:
[`.vv/ci/continuous-ship.md`](../.vv/ci/continuous-ship.md), [`.vv/deploy/VERCEL.md`](../.vv/deploy/VERCEL.md)

**GitHub Actions owns every deploy of `public/`.** Vercel's own Git integration stays connected (Deploy
Hooks need it) but its automatic deploy on push to `main` is switched off in `vercel.json`
(`git.deploymentEnabled.main: false`). One merged commit ⇒ one Actions-gated deploy. The ADK/Cloud Run
backend deploys independently (CLAUDE.md invariant 11) — nothing in `deploy.yml` touches GCP.

Secrets are referenced **by name only**: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
(CLI path), `VERCEL_DEPLOY_HOOK_PROD` (hook fallback), `VERCEL_AUTOMATION_BYPASS_SECRET` (optional, preview
protection). Values live in 1Password Environment `dev` and GitHub Actions secrets — never in git, chat,
or issues. **Status: secrets not set as of 2026-09-08 (issue #27)** — until an owner sets them every run
stops after `gates` with a `::notice` naming the missing secrets.

**Deploy notifications (webhooks)** are separate from Deploy Hooks: Vercel POSTs
`deployment.created` / `succeeded` / `error` / … to your HTTPS endpoint. Secret name
`VERCEL_WEBHOOK_SECRET` (`op://dev/VERCEL_WEBHOOK_SECRET/credential`). Setup + HMAC verify:
[vercel-webhooks.md](vercel-webhooks.md) (issue #37). UI:
<https://vercel.com/1digital-design/hop-ultrasonic/settings/webhooks>.

## (a) Architecture

```text
push / merge to main
   │
   ▼
CI — no breaking changes  (ci.yml: autoroute · static_gates · tests · mdc_check · pr_issue_ref)
   │ workflow_run: completed && conclusion == success && head_branch == main
   ▼
Deploy — dev → test → prod  (deploy.yml, concurrency group deploy-main, cancel-in-progress: false)
   ├─ secrets_check ── outputs has_cli / has_hook / target   (names only, never values; never fails)
   ├─ gates ────────── ci_static_gates.sh · autoroute_dev.sh · pytest tests -q   (re-run on DEPLOY_REF)
   ├─ deploy_dev ───── env dev:  vercel pull --yes --environment=preview → vercel build → vercel deploy --prebuilt → preview_url
   ├─ test ─────────── env test: scripts/deploy_smoke.sh <preview_url>   [x-vercel-protection-bypass when BYPASS set]
   └─ deploy_prod ──── env production:
                        CLI  : vercel pull --yes --environment=production → vercel build --prod → vercel deploy --prebuilt --prod
                        hook : (workflow_dispatch only) curl -fsS -X POST $VERCEL_DEPLOY_HOOK_PROD → {job:{id,state:PENDING}}
                               → poll ≤ 5 min until prod serves THIS checkout (ETag == md5 of public/ files)
                        then : SMOKE_PUBLIC_DIR=public scripts/deploy_smoke.sh $PROD_URL   (smoke + build identity)
```

| Trigger | When | `target` | Ref deployed |
|---------|------|----------|--------------|
| `workflow_run` | `CI — no breaking changes` completed with `conclusion == success` on `main` | `prod` (all five jobs) | `github.event.workflow_run.head_sha` — the commit CI actually tested |
| `workflow_dispatch` | manual, from the Actions tab or `gh workflow run` | `dev` \| `test` \| `prod` (default `prod`) | input `ref` (default: the default branch) |

Job gating (every job also carries the run-level success guard):

| Job | Runs when |
|-----|-----------|
| `secrets_check`, `gates` | always |
| `deploy_dev` | `has_cli == true` |
| `test` | `deploy_dev` succeeded and `target != dev` |
| `deploy_prod` | `target == prod`, `gates` green, and (`test` green **or** — **`workflow_dispatch` only** — `test` skipped because the CLI secrets are absent) and (`has_cli` **or** `has_hook`) |

An automatic (`workflow_run`) ship therefore always goes dev → test → prod and needs the CLI secrets. With
only the hook secret set, `workflow_run` stops after `gates` with `::notice title=Deploy hook only::…`; a human
ships by dispatching `target=prod`.

The prod URL is repo variable `PROD_URL` (Settings → Secrets and variables → Actions → Variables), defaulting
to `https://hop-ultrasonic-1digital-design.vercel.app`. It is public config, not a secret.

Why the hook path is a dispatch-only fallback, not the default: a Deploy Hook makes Vercel build `main` from
its own Git checkout, so (1) there is no preview, hence no dev → test stage, (2) the dispatch `ref` input is
ignored (the workflow prints a `::warning`), and (3) without a token the job id cannot be queried. The poll
therefore does **not** accept "the prod URL passes smoke" — the previous build already does — it accepts only
"the prod URL serves exactly this checkout": `scripts/deploy_smoke.sh` with `SMOKE_PUBLIC_DIR=public` compares
the served `ETag` of `/`, `/patch.json` and `/manifest.webmanifest` with the md5 (or sha1) of the local files
(Vercel serves static files with `ETag == md5(content)`; observed 2026-09-08, see Sources) and keeps polling
until they match, failing after 5 min with nothing marked shipped. The same identity check runs in `test`
(preview must be this checkout) and in the final production smoke on both paths. The CLI path additionally
deploys exactly the Actions checkout and prints its URL.

`scripts/deploy_smoke.sh` never follows redirects (`--max-redirs 0`, no `-L`): curl forwards custom `-H`
headers — unlike `Authorization`/`Cookie` — to every redirect target including other hosts, so following a
redirect could leak `VERCEL_AUTOMATION_BYPASS_SECRET` off-host. A 3xx is a failure that prints the `Location`
it refused. The bypass secret is also refused over plaintext `http://` (loopback excepted, for offline tests).

## (b) One-time Vercel setup

At <https://vercel.com/1digital-design/hop-ultrasonic/settings/git>:

1. **Connect the GitHub repository** `team-project-pikachu/IoT-ASP` (team `1digital-design`, project
   `hop-ultrasonic`). Keep the integration connected — Deploy Hooks are delivered through it.
2. **Production branch:** `main`.
3. **Automatic deployments for `main` stay off** — not via the dashboard, but via the committed
   `vercel.json` key `"git": { "deploymentEnabled": { "main": false } }`. Unlisted branches still get Vercel
   PR previews; that is harmless and `ci.yml`/`deploy.yml` never rely on them.
   **Do not** add `"github": { "enabled": false }` — that disconnects the GitHub integration entirely and
   Deploy Hooks stop firing (vercel/vercel discussion #8619).
4. **Create a Deploy Hook** named `gh-actions-prod` on ref `main` — Settings → Git → Deploy Hooks (UI), or
   `vercel deploy-hooks create gh-actions-prod --ref main` where the CLI supports it. Copy the hook URL
   **once** into 1Password (`op://dev/VERCEL_DEPLOY_HOOK_PROD/credential`) and then into the GitHub secret
   `VERCEL_DEPLOY_HOOK_PROD`. Hook URLs embed the project id and a key: treat them as secrets.
   Triggering returns `{"job":{"id":"…","state":"PENDING","createdAt":…}}`; the workflow prints only
   `id` and `state`.
5. (Optional) If Deployment Protection is enabled for previews, create a Protection Bypass for Automation
   secret (Settings → Deployment Protection) and store it as GitHub secret `VERCEL_AUTOMATION_BYPASS_SECRET`.
   `scripts/deploy_smoke.sh` sends it as the `x-vercel-protection-bypass` header when `BYPASS` is set.

## (c) Token path (CLI deploys)

1. Create a Vercel token at <https://vercel.com/account/settings/tokens> **scoped to team `1digital-design`**
   (an unscoped personal token cannot deploy the team project). Give it a name like `gh-actions IoT-ASP`
   and an expiry.
2. Store it in 1Password Environment `dev` as item `VERCEL_TOKEN` (field `credential`).
3. Get the ids: in a local clone run `vercel link` (choose team `1digital-design`, project `hop-ultrasonic`)
   and read `.vercel/project.json` → `orgId` (`team_…`) and `projectId` (`prj_…`). `.vercel/` is gitignored.
   Store them as 1Password items `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID`. This doc keeps placeholders only:
   `VERCEL_ORG_ID: <team_… placeholder>`, `VERCEL_PROJECT_ID: <prj_… placeholder>`.
4. Push the names into GitHub Actions secrets — value on **stdin**, never on the command line:

   ```bash
   op read "op://dev/VERCEL_TOKEN/credential"            | gh secret set VERCEL_TOKEN            --repo team-project-pikachu/IoT-ASP
   op read "op://dev/VERCEL_ORG_ID/credential"           | gh secret set VERCEL_ORG_ID           --repo team-project-pikachu/IoT-ASP
   op read "op://dev/VERCEL_PROJECT_ID/credential"       | gh secret set VERCEL_PROJECT_ID       --repo team-project-pikachu/IoT-ASP
   op read "op://dev/VERCEL_DEPLOY_HOOK_PROD/credential" | gh secret set VERCEL_DEPLOY_HOOK_PROD --repo team-project-pikachu/IoT-ASP
   ```

   `bash scripts/vercel_secrets_check.sh` prints which of the names are set in your shell (never values) and
   this recipe. `scripts/op_secrets_to_gh.sh` (integrator-owned) automates `op inject` → `gh secret set -f`.
5. Verify from the Actions tab: run the workflow with `target=dev` (section e) and check that
   `secrets_check` prints `has_cli=true` and that `deploy_dev` posts a preview URL to the run summary.

Vercel CLI in CI is pinned to the current major, `npm i -g vercel@59` (npm `latest` = 59.11.7 on
2026-09-08, `engines.node >= 18`), on `actions/setup-node@v4` Node 20. Bump the pin deliberately together
with `tests/test_deploy_workflow.py` (DP-07). Commands are non-interactive: `vercel pull --yes`,
`vercel build`, `vercel deploy --prebuilt` (no double build), token via `--token=${{ secrets.VERCEL_TOKEN }}`.

## (c′) Option B — 1Password service account instead of copied secrets (owner decision)

Prior-art check (`docs/PRIOR_ART.md`): 1Password ships an official GitHub Action that resolves `op://`
references at run time with a **service account**, so the four Vercel secrets never have to be copied
into GitHub at all — only `OP_SERVICE_ACCOUNT_TOKEN` is stored, and rotation happens in 1Password.

```yaml
# inside a deploy job, before the Vercel CLI steps
- uses: 1password/load-secrets-action/configure@v4
  with:
    service-account-token: ${{ secrets.OP_SERVICE_ACCOUNT_TOKEN }}
- uses: 1password/load-secrets-action@v4
  id: op
  with:
    export-env: false
  env:
    VERCEL_TOKEN: op://dev/Vercel deploy token gh-actions/credential
    VERCEL_ORG_ID: op://dev/Vercel hop-ultrasonic/orgId
    VERCEL_PROJECT_ID: op://dev/Vercel hop-ultrasonic/projectId
    VERCEL_DEPLOY_HOOK_PROD: op://dev/Vercel deploy hook gh-actions-prod/credential
# then reference ${{ steps.op.outputs.VERCEL_TOKEN }} etc. instead of ${{ secrets.VERCEL_TOKEN }}
```

Not enabled by default: the owner's tooling policy asks that service accounts be agreed first. To adopt it,
create a service account with read access to vault `dev` (1Password → Developer → Service accounts), store
its token as the single GitHub secret `OP_SERVICE_ACCOUNT_TOKEN`, and switch `secrets_check` / `deploy_*`
in `deploy.yml` to the step outputs above. Until then Option A (`scripts/op_secrets_to_gh.sh`) remains the path.
Source: https://www.1password.dev/ci-cd/github-actions (Context7 `/websites/1password_dev`).

## (d) GitHub Environments

Settings → Environments → **New environment**, create `dev`, `test`, `production` (names must match
`deploy.yml`). Recommended protection on `production`: **Required reviewers** (up to 6 people/teams; a single
approval releases the job) and, optionally, a deployment-branch rule restricting to `main`. Leave `dev` and
`test` unprotected so a push to `main` flows through them unattended. Environment-scoped secrets are not
required — the workflow reads repository-level secrets — but you may move `VERCEL_TOKEN` into `production`
and `dev` if you want per-environment tokens later.

## (e) Running it by hand (`workflow_dispatch`)

```bash
# stop after the dev preview (first thing to try after setting secrets)
gh workflow run "Deploy — dev → test → prod" --repo team-project-pikachu/IoT-ASP -f target=dev
# preview + smoke
gh workflow run "Deploy — dev → test → prod" --repo team-project-pikachu/IoT-ASP -f target=test
# full ship of a specific commit
gh workflow run "Deploy — dev → test → prod" --repo team-project-pikachu/IoT-ASP -f target=prod -f ref=<sha>
gh run list --workflow "Deploy — dev → test → prod" --repo team-project-pikachu/IoT-ASP
```

Notes: `workflow_run` only ever uses the `deploy.yml` from the **default branch**, so edits on a feature
branch are inert until merged — test them with a dispatch after merge. The `ref` input is honoured by the CLI
path; the hook path always builds `main` on Vercel.

## (f) Rollback / promote

```bash
vercel rollback <deployment-url-or-id> --scope 1digital-design   # revert production to a previous deployment
vercel promote  <deployment-url-or-id> --scope 1digital-design   # move an existing, verified deployment to production without rebuilding
```

Blue/green by hand: `URL=$(vercel --prod --skip-domain)` → verify `URL` (`bash scripts/deploy_smoke.sh "$URL"`)
→ `vercel promote "$URL"`. Rolling back in the dashboard (Deployments → ⋯ → *Instant Rollback*) is equivalent.
A rollback does not change `main`; follow it with a revert commit so the next `workflow_run` does not re-ship
the bad build.

## (g) Evidence expectations

Every real run refreshes `.vv/ci/continuous-ship.md`: run URL, per-job result (`secrets_check` outputs,
`gates`, `deploy_dev` preview URL, `test`, `deploy_prod` prod URL), local command exit codes, and the
`secrets not set …` status line until it is no longer true. `.vv/deploy/VERCEL.md` records what exists on the
Vercel side (project, team, prod URL, hook **name**, environment names) with id **placeholders** only. Never
paste token values, hook URLs, or `.vercel/project.json` contents into evidence, issues, or chat.

Local pre-flight before opening a PR that touches this pipeline:

```bash
python3 -m pytest tests/test_deploy_workflow.py -q
bash -n scripts/deploy_smoke.sh scripts/vercel_secrets_check.sh
bash scripts/deploy_smoke.sh https://hop-ultrasonic-1digital-design.vercel.app   # needs network
SMOKE_PUBLIC_DIR=public bash scripts/deploy_smoke.sh https://hop-ultrasonic-1digital-design.vercel.app   # + build identity: passes only when prod == this checkout
bash scripts/vercel_secrets_check.sh
```

## Sources

- Context7 `/vercel/vercel` — `skills/vercel-cli/references/ci-automation.md` (standard CI pattern
  `vercel pull --yes --environment=production` → `vercel build --prod` → `vercel deploy --prebuilt --prod`;
  `URL=$(vercel deploy --prod)` — stdout is the URL, stderr is progress), `skills/vercel-cli/references/deployment.md`
  (blue/green `--skip-domain` → `vercel promote`; `vercel rollback`), `packages/config/example/vercel.ts`
  (`git.deploymentEnabled: { <branch>: false }`; unlisted branches deploy automatically).
- Vercel KB — *How can I use GitHub Actions with Vercel?* <https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel>
  (`--prebuilt` avoids double builds; disable Git-integration deploys via `vercel.json` `git.deploymentEnabled`).
- Vercel docs — *Creating & Triggering Deploy Hooks* <https://vercel.com/docs/deploy-hooks>
  (`curl -X POST <hook>` → `{"job":{"id":…,"state":"PENDING","createdAt":…}}`; `?buildCache=false`).
- Vercel docs — *Git Configuration* <https://vercel.com/docs/project-configuration/git-configuration>;
  *Deploying GitHub Projects with Vercel* <https://vercel.com/docs/git/vercel-for-github>.
- Vercel docs — *Protection Bypass for Automation*
  <https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection/protection-bypass-automation>
  (`x-vercel-protection-bypass` header, `VERCEL_AUTOMATION_BYPASS_SECRET`).
- GitHub discussion vercel/vercel #8619 <https://github.com/vercel/vercel/discussions/8619>
  (`github.enabled: false` stops Deploy Hooks from working).
- npm registry <https://registry.npmjs.org/vercel/latest> queried 2026-09-08 → `59.11.7`, `engines.node >= 18`.
- Build identity — observed 2026-09-08 with `curl -sS -D - -o /dev/null https://hop-ultrasonic-1digital-design.vercel.app/patch.json`
  and `md5sum public/patch.json`: Vercel's static `etag` (`"5e3a…835f"`) equals the md5 of the file content
  (same for `/manifest.webmanifest`; `/` differed only because the deployed build predates the checkout).
  `scripts/deploy_smoke.sh` accepts md5 **or** sha1 and fails loudly if the scheme ever changes. Related:
  Vercel changelog *Optimized CDN caching and deploying of immutable static assets*
  <https://vercel.com/changelog/optimized-cdn-caching-and-deploying-of-immutable-static-assets> (static files are
  content-addressed across deployments).
- curl redirect semantics — curl withholds only `Authorization`/`Cookie` on cross-origin redirects (`--location-trusted`
  re-enables them); user-supplied `-H` headers are sent to every redirect target: curl manual `--location`,
  `--location-trusted`, `--max-redirs` <https://curl.se/docs/manpage.html>; summary in
  <https://proxidize.com/blog/curl-send-headers/>. Hence `--max-redirs 0` and no `-L` in `scripts/deploy_smoke.sh`.
- GitHub docs — *Events that trigger workflows → `workflow_run`*
  <https://docs.github.com/actions/using-workflows/events-that-trigger-workflows> (default-branch workflow
  file, `conclusion`, `branches:` filter, `head_branch`, `head_sha`).
- GitHub docs — *Workflow syntax* <https://docs.github.com/actions/reference/workflows-and-actions/workflow-syntax>
  (`workflow_dispatch.inputs` `type: choice`; `jobs.<job_id>.environment` `name`/`url`; `concurrency`).
- GitHub docs — *Contexts → Context availability* <https://docs.github.com/actions/reference/workflows-and-actions/contexts>
  and actionlint `docs/checks.md` *Availability of contexts and special functions*
  <https://github.com/rhysd/actionlint/blob/main/docs/checks.md> (`env` is not available in
  `jobs.<job_id>.if` / `jobs.<job_id>.environment` — hence `vars.PROD_URL || …` and the `target` job output).
- GitHub docs — *Managing environments for deployment*
  <https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment>
  (required reviewers, up to 6, one approval suffices).
- Repo: `.github/workflows/ci.yml`, `vercel.json`, `scripts/ci_static_gates.sh`, `.vv/ci/EVIDENCE.md`,
  `.claude/rules/ci-and-workflows.md`, GitHub issue #27.
