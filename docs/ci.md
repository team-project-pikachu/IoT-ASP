# CI — no breaking changes (issue-linked PRs)

GitHub Actions workflows:

| Workflow | Path | Role |
|----------|------|------|
| **CI — no breaking changes** | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Gates on PR + push to `main` |
| **Deploy — continuous MVP ship** | [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) | After green CI on `main` push → Vercel preview then prod |

## When it runs

| Event | Branches | Notes |
|-------|----------|--------|
| `pull_request` (`opened` / `synchronize` / `reopened`) | `main` | **CI only** — full gates + **issue reference** check (no deploy) |
| `push` | `main` | CI gates; on success, `workflow_run` starts **Deploy** |

Issue-linked PRs are the intended path for Project 5 Todo work (#12, #16, #17, research #9, design #13). Use the [PR template](../.github/PULL_REQUEST_TEMPLATE.md) with `Fixes #N` / `Closes #N` / `Related: #N`.

**Agent habit:** after each non-breaking MVP slice passes local sim (`autoroute_dev` + `ci_static_gates`), **commit and push that slice** on an issue-linked PR — do not accumulate a huge uncommitted tree.

## Jobs (CI)

1. **`autoroute`** — asserts `vol_hard_max == 100` first (legacy “hard max 20” drift), installs `services/autoroute-adk/requirements.txt`, runs `bash scripts/autoroute_dev.sh`, then import smoke for clamps / sudden_freq / Hold refuse.
2. **`static_gates`** — `bash scripts/ci_static_gates.sh`: Hold/Manual in `public/index.html`, no obvious API-key patterns in HTML, `public/patch.json` `schemaVersion: 1`, clamp constants.
3. **`pr_issue_ref`** (PR only) — fails if title/body lack an issue ref (`#N` or `Fixes`/`Closes`/`Resolves`/`Related` `#N`).

## Continuous ship (Deploy)

**Policy:** MVP **non-breaking** deltas → ship continuously via Actions after green CI. **Breaking** contract/clamp/schema changes → open a [Project 5](https://github.com/orgs/team-project-pikachu/projects/5) issue first (never silent break).

| Guardrail | Behavior |
|-----------|----------|
| CI must be green | Deploy triggers only on `workflow_run` conclusion `success` for push to `main` |
| Hold / clamp / schema | Deploy **re-runs** `autoroute_dev.sh` + `ci_static_gates.sh` (never skipped) |
| PR path | CI only — no Vercel promote from PR workflows |
| Secrets missing | Deploy job **skips** with a notice; workflow stays green; manual path remains |

### Required GitHub repository secrets

Set under **Settings → Secrets and variables → Actions** for `team-project-pikachu/IoT-ASP`:

| Secret name | Purpose | How to obtain |
|-------------|---------|----------------|
| `VERCEL_TOKEN` | Authenticate Vercel CLI in Actions | Vercel → Account Settings → Tokens (create; store in 1Password `dev`, then `gh secret set`) |
| `VERCEL_ORG_ID` | Team / org scope | From linked project `.vercel/project.json` → `orgId` (hop-ultrasonic link on Studio) |
| `VERCEL_PROJECT_ID` | Target project (`hop-ultrasonic`) | From `.vercel/project.json` → `projectId` |

Until all three are present, Actions will print:

> Auto-deploy skipped — missing GitHub secrets: …

and leave production unchanged.

### Manual path (no Actions token)

```bash
# Preferred mirror root (already linked):
cd /path/to/hop-ultrasonic
vercel --prod

# Or after syncing IoT-ASP public/ + vercel.json into that project.
```

Prod alias: **https://hop-ultrasonic.vercel.app/**

Evidence: [`.vv/ci/continuous-ship.md`](../.vv/ci/continuous-ship.md).

## Local reproduction

```bash
bash scripts/ci_static_gates.sh
bash scripts/autoroute_dev.sh
```

Evidence package: [`.vv/ci/`](../.vv/ci/).

## Out of scope

- Heavy Firecrawl / link crawls
- Live GCP / Vertex / ADK Agent Engine deploy (separate from Vercel)
- Editing SEBoK plan files
