# Continuous ship evidence — GitHub Actions → Vercel

**UTC:** `2026-09-08T00:42:00Z` (Studio re-check)  
**Repo:** `team-project-pikachu/IoT-ASP`  
**Config:** `.github/workflows/deploy.yml` + `.github/workflows/ci.yml`  
**Docs:** `docs/ci.md`  
**Rule:** `.cursor/rules/asp-backend-vv-ci.mdc` (MVP non-breaking → continuous ship; breaking → Project 5 first)

## Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| CS-01 | Deploy via **GitHub Actions** (not CLI-only) | **PASS** — `deploy.yml` present |
| CS-02 | Trigger after CI success on `main` (`workflow_run`) | **PASS** — filters success + `push` + `main` |
| CS-03 | Re-run `autoroute_dev` + static gates before deploy | **PASS** — `gates` job; never skip |
| CS-04 | Preview/test then production | **PASS** — `vercel deploy` then `vercel deploy --prod` |
| CS-05 | Secrets `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` | **BLOCKED** — none on repo; no deploy token in 1Password |
| CS-06 | PR path = CI only | **PASS** — deploy only on push→main CI success |
| CS-07 | Manual `vercel --prod` retained when secrets absent | **PASS** — `docs/ci.md` |

## Secret status (verified 2026-09-08)

```text
gh secret list -R team-project-pikachu/IoT-ASP
# (empty — no VERCEL_* secrets)
```

| Secret | Present on GitHub? |
|--------|--------------------|
| `VERCEL_TOKEN` | **No** |
| `VERCEL_ORG_ID` | **No** |
| `VERCEL_PROJECT_ID` | **No** |

**Auto-deploy: NOT LIVE** until all three secrets are set. Workflow runs gates then skips Vercel with a notice.

### 1Password lookup (this pass)

| Source | Result |
|--------|--------|
| Vault name `dev` | **Does not exist** as an `op` vault |
| 1Password Environment **`dev`** | Present; **no** `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` (has `BLOB_READ_WRITE_TOKEN` only — Blob RW, not Actions deploy) |
| Vault **Development** | Item `Vercel Blob — tb3` → Blob RW token only |
| Vault **self** | Item `Vercel` → LOGIN (account/OTP); **no** API/deploy token field |
| Cowork-CLI-Keys / Keystore / Private / Shared | No Vercel deploy-token items |
| `~/.config/op/fleet.env` | No `VERCEL_*` keys |

**Do not invent tokens.** Create a Vercel token in the dashboard (or `vercel tokens`), store it in Environment `dev` as `VERCEL_TOKEN`, then `gh secret set`.

### Resolved IDs (non-secret; ready to set once token exists)

From Studio `hop-ultrasonic/.vercel/project.json` and `vercel project ls --scope 1digital-design` (CLI user `1digitaldesign`, team **1digital-design**):

| Field | Value |
|-------|--------|
| `VERCEL_ORG_ID` | `team_FMcobi2jOg60hmmaZMenbAnp` |
| `VERCEL_PROJECT_ID` | `prj_6LqmrGuRMiy1V5sZ7wVchuUv7Ekg` |
| projectName | `hop-ultrasonic` |
| prod alias | https://hop-ultrasonic.vercel.app/ |

IoT-ASP has no separate `.vercel` link; continuous ship targets the **hop-ultrasonic** project.

## Operator next steps (least privilege)

1. **Create** a Vercel deploy token (Account Settings → Tokens, or `vercel tokens add`) scoped to team `1digital-design` / project `hop-ultrasonic`. Prefer a dedicated Actions token (not session cookie).
2. **Store** in 1Password Environment `dev` as concealed `VERCEL_TOKEN` (optional: also store `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` for operators).
3. **Set GitHub secrets** (values never paste into issues/chat):

```bash
# Token from 1Password — do not echo
op read 'op://…/VERCEL_TOKEN' | gh secret set VERCEL_TOKEN -R team-project-pikachu/IoT-ASP

printf '%s' 'team_FMcobi2jOg60hmmaZMenbAnp' \
  | gh secret set VERCEL_ORG_ID -R team-project-pikachu/IoT-ASP

printf '%s' 'prj_6LqmrGuRMiy1V5sZ7wVchuUv7Ekg' \
  | gh secret set VERCEL_PROJECT_ID -R team-project-pikachu/IoT-ASP

gh secret list -R team-project-pikachu/IoT-ASP   # expect three VERCEL_* names only
```

4. Push or re-run green CI on `main` → Deploy workflow should preview then `--prod`.
5. Until then: manual promote via hop-ultrasonic CLI remains valid (see `.vv/deploy/VERCEL.md`).

## Local gate evidence (pre-ship)

| Check | Result |
|-------|--------|
| `bash scripts/ci_static_gates.sh` | exit 0 (prior pass) |
| `bash scripts/autoroute_dev.sh` | exit 0 — `DRY-RUN OK` (prior pass) |

## Prod URL (current alias)

**https://hop-ultrasonic.vercel.app/** — see `.vv/deploy/VERCEL.md` for last manual promote.

## Tracking

Project 5: https://github.com/team-project-pikachu/IoT-ASP/issues/27 — **Set Vercel Actions secrets for continuous MVP ship**
