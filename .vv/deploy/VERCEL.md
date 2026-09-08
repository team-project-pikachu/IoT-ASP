# Vercel deploy evidence — project `hop-ultrasonic` (team `1digital-design`)

**Config item:** Vercel project `hop-ultrasonic` ↔ GitHub `team-project-pikachu/IoT-ASP`, driven by
`.github/workflows/deploy.yml` (issue #27)
**Docs:** `docs/deploy.md`
**Date:** 2026-09-08 (UTC)
**Status:** `secrets not set as of 2026-09-08 (issue #27)`

## What exists (2026-09-08)

| Item | Value / state |
|------|---------------|
| Team | `1digital-design` |
| Project | `hop-ultrasonic` — settings: `https://vercel.com/1digital-design/hop-ultrasonic/settings/git` |
| Production URL | `https://hop-ultrasonic-1digital-design.vercel.app` (repo variable `PROD_URL` may override) |
| Served content | `public/` static PWA; `vercel.json` `cleanUrls`, `trailingSlash: false`, security headers, manifest `Content-Type` |
| Git integration | connected to `team-project-pikachu/IoT-ASP`, production branch `main`; automatic deploy on push to `main` **disabled by `vercel.json` `git.deploymentEnabled.main: false`** (PR previews for other branches unchanged) |
| Deploy Hook | **name** `gh-actions-prod`, ref `main` — to be created by an owner (URL is a secret; not recorded) |
| Deployment Protection | unknown/default; if previews are protected, set `VERCEL_AUTOMATION_BYPASS_SECRET` |
| Live smoke (read-only) | `bash scripts/deploy_smoke.sh https://hop-ultrasonic-1digital-design.vercel.app` → exit 0 on 2026-09-08 |

## Required GitHub Actions secret NAMES

| Name | Source | Status 2026-09-08 |
|------|--------|-------------------|
| `VERCEL_TOKEN` | vercel.com/account/settings/tokens, scoped to team `1digital-design` → 1Password `op://dev/VERCEL_TOKEN/credential` | not set |
| `VERCEL_ORG_ID` | `vercel link` → `.vercel/project.json` `orgId` — `<team_… placeholder>` (id not invented) | not set |
| `VERCEL_PROJECT_ID` | `vercel link` → `.vercel/project.json` `projectId` — `<prj_… placeholder>` (id not invented) | not set |
| `VERCEL_DEPLOY_HOOK_PROD` | Deploy Hook `gh-actions-prod` URL | not set |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | Vercel → Deployment Protection → Protection Bypass for Automation (optional) | not set |

Set them with the stdin recipe in `scripts/vercel_secrets_check.sh` / `docs/deploy.md` §c, or
`scripts/op_secrets_to_gh.sh` (integrator-owned).

## GitHub Environments to create

| Environment | Protection |
|-------------|------------|
| `dev` | none |
| `test` | none |
| `production` | optional required reviewers (≤ 6, one approval suffices); optional branch rule `main` |

## Procedure (owner, one time)

1. `docs/deploy.md` §b — connect repo, production branch `main`, create Deploy Hook `gh-actions-prod`.
2. `docs/deploy.md` §c — team-scoped token → 1Password `dev` → `gh secret set` the four names.
3. `docs/deploy.md` §d — create the three GitHub Environments.
4. `gh workflow run "Deploy — dev → test → prod" --repo team-project-pikachu/IoT-ASP -f target=dev`, then
   `-f target=prod`; paste run URLs + job results (no secrets) into `.vv/ci/continuous-ship.md`.

## Pass/fail

| Item | Status |
|------|--------|
| `vercel.json` `git.deploymentEnabled.main == false`, headers preserved (DP-11) | **PASS** (local test) |
| Production URL serves the smoke contract (Hold / Manual, `holdManual`, `schemaVersion 1`, headers) | **PASS** (2026-09-08, current Vercel-deployed build) |
| Secrets + Deploy Hook + Environments | **PENDING** — `secrets not set as of 2026-09-08 (issue #27)` |

## Prior manual production evidence

Before Actions ownership was enabled, the contour-mirror plus
burst/`micDiff` build was promoted manually to
`https://hop-ultrasonic.vercel.app/` as deployment
`dpl_7KFoJW72gnrnpvyTSV1LC6NGrJbK`. This is historical evidence only;
the dev → test → production workflow above is authoritative once its
named secrets and environments are configured.
