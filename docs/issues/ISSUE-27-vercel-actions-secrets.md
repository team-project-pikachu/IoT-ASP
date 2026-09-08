# ISSUE-27 — Set Vercel Actions secrets for continuous MVP ship

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/27  
**Classification:** docs/ops (Balanced) — **instructions only, no secret values**

## Exact secret NAMES to set

| Name | Where to set | 1Password Environment `dev` item (reference) |
|------|----------------|-----------------------------------------------|
| `VERCEL_TOKEN` | GitHub repo → Settings → Secrets and variables → Actions | `op://dev/VERCEL_TOKEN/credential` |
| `VERCEL_ORG_ID` | same | `op://dev/VERCEL_ORG_ID/credential` |
| `VERCEL_PROJECT_ID` | same | `op://dev/VERCEL_PROJECT_ID/credential` |
| `VERCEL_DEPLOY_HOOK_PROD` | same (hook fallback) | `op://dev/VERCEL_DEPLOY_HOOK_PROD/credential` |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | optional | Protection Bypass for Automation |

Team/project: Vercel team **`1digital-design`**, project **`hop-ultrasonic`**. See `.vv/deploy/VERCEL.md` and `docs/deploy.md`.

## Did

- Documented names + recipe in `docs/deploy.md`, `.vv/deploy/VERCEL.md`, `scripts/vercel_secrets_check.sh`.
- Workflow already skips deploy with `::notice` when secrets missing (does not fail CI).

## Didn't

- Create or paste any token/org/project values.
- Claim Actions prod ship is live until `gh secret list` shows the three required names.

## Next

1. Owner creates team-scoped Vercel token → 1Password `dev`.
2. `gh secret set VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` (stdin).
3. `gh workflow run "Deploy — dev → test → prod" -f target=dev` then `prod`.
