# ISSUE-27 — Set Vercel Actions secrets for continuous MVP ship

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/27  
**Classification:** docs/ops (Balanced) — **names only**  
**Status:** ORG/PROJECT present in Actions; **TOKEN still missing** (Balanced PR8 inventory)
**Classification:** docs/ops — **names only**  
**Status:** blocked/partial — docs + name-presence checker (stack PR3); values OWNER-GATED until trio exists and preview/prod deploy succeeds

## Exact secret NAMES

| Name | Where | 1Password reference (names only) |
|------|-------|----------------------------------|
| `VERCEL_TOKEN` | GitHub Actions secrets | Prefer Environment `dev` key; else Development vault login item title `vercel - hop-ultrasonic` |
| `VERCEL_ORG_ID` | same | `op://dev/VERCEL_ORG_ID/credential` or same item / env |
| `VERCEL_PROJECT_ID` | same | `op://dev/VERCEL_PROJECT_ID/credential` or same item / env |
| `VERCEL_DEPLOY_HOOK_PROD` | optional hook fallback | `op://dev/VERCEL_DEPLOY_HOOK_PROD/credential` |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | optional | Protection Bypass for Automation |
| `VERCEL_WEBHOOK_SECRET` | optional (#37) | optional |

Team/project: Vercel team **`1digital-design`**, project **`hop-ultrasonic`**. See `.vv/deploy/VERCEL.md` and `docs/deploy.md`.
| Name | Where | 1Password `dev` reference |
|------|-------|---------------------------|
| `VERCEL_TOKEN` | GitHub Actions secrets | `op://dev/VERCEL_TOKEN/credential` |
| `VERCEL_ORG_ID` | same | `op://dev/VERCEL_ORG_ID/credential` |
| `VERCEL_PROJECT_ID` | same | `op://dev/VERCEL_PROJECT_ID/credential` |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | optional | Protection Bypass |
| `VERCEL_WEBHOOK_SECRET` | optional (#37) | `op://dev/VERCEL_WEBHOOK_SECRET/credential` |

## Live inventory (2026-09-08, names only — no values)

| Source | Observation |
|--------|-------------|
| `gh secret list` | `VERCEL_ORG_ID` PRESENT · `VERCEL_PROJECT_ID` PRESENT · **`VERCEL_TOKEN` MISSING** |
| 1Password vault **Development** | Item title **`vercel - hop-ultrasonic`** (login-style). Related titles seen: `Vercel Blob — tb3` (different product). |
| Discrete `op://dev/VERCEL_*` Environment keys | Not confirmed in this pass — owner should verify or split fields from the login item |

## Did

- Documented names + recipe in `docs/deploy.md`, `.vv/deploy/VERCEL.md`, `scripts/vercel_secrets_check.sh`, `scripts/gh_secrets_names_check.sh`
- Workflow already skips deploy with `::notice` when secrets missing (does not fail CI)
- PR8: refreshed inventory + honest Actions presence (ORG/PROJECT yes, TOKEN no)

## Didn't
- Create or paste any token/org/project values
- Run `gh secret set` (needs explicit owner authorization + resolved op values without printing)
- Claim Actions prod ship is live until `gh secret list` shows the three required names
## Next
1. Owner confirms `VERCEL_TOKEN` source (Environment `dev` vs `vercel - hop-ultrasonic` credential)
2. Pipe into `gh secret set VERCEL_TOKEN` (stdin only)
3. `bash scripts/gh_secrets_names_check.sh` → expect trio PRESENT
4. `gh workflow run "Deploy — dev → test → prod" -f target=dev` then `prod`
- `docs/deploy.md`, `.vv/deploy/VERCEL.md`, `scripts/vercel_secrets_check.sh` (local env)
- `scripts/gh_secrets_names_check.sh` — `gh secret list` presence of **names** only
- Paste or invent any token/org/project values
- Claim continuous ship is live
1. Owner stores values in 1Password `dev`
2. Pipe into `gh secret set` (stdin)
3. `gh workflow run "Deploy — dev → test → prod" -f target=dev`
