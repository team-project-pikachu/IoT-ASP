# ISSUE-27 — Set Vercel Actions secrets for continuous MVP ship

**Classification:** docs/ops — **names only**  
**Status:** docs + name-presence checker (stack PR3); values OWNER-GATED

## Exact secret NAMES

| Name | Where | 1Password `dev` reference |
|------|-------|---------------------------|
| `VERCEL_TOKEN` | GitHub Actions secrets | `op://dev/VERCEL_TOKEN/credential` |
| `VERCEL_ORG_ID` | same | `op://dev/VERCEL_ORG_ID/credential` |
| `VERCEL_PROJECT_ID` | same | `op://dev/VERCEL_PROJECT_ID/credential` |
| `VERCEL_DEPLOY_HOOK_PROD` | optional hook fallback | `op://dev/VERCEL_DEPLOY_HOOK_PROD/credential` |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | optional | Protection Bypass |
| `VERCEL_WEBHOOK_SECRET` | optional (#37) | `op://dev/VERCEL_WEBHOOK_SECRET/credential` |

## Did

- `docs/deploy.md`, `.vv/deploy/VERCEL.md`, `scripts/vercel_secrets_check.sh` (local env)
- `scripts/gh_secrets_names_check.sh` — `gh secret list` presence of **names** only
- Inventory note (stack PR5): 1Password vault **Development** has item title `vercel - hop-ultrasonic` (login-style `credential` field). Discrete Environment `dev` keys `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` may still need owner creation — **values never committed**.

## Didn't

- Paste or invent any token/org/project values
- Claim continuous ship is live
- Assume Development login item ≡ Actions secret set

## Next

1. Owner confirms whether `op://dev/VERCEL_TOKEN|ORG_ID|PROJECT_ID` exist as Environment vars, or whether to split from `vercel - hop-ultrasonic`
2. Pipe into `gh secret set` (stdin)
3. `gh workflow run "Deploy — dev → test → prod" -f target=dev`
