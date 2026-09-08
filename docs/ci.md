# CI — no breaking changes (issue-linked PRs)

GitHub Actions workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

## When it runs

| Event | Branches | Notes |
|-------|----------|--------|
| `pull_request` (`opened` / `synchronize` / `reopened`) | `main` | Full gates + **issue reference** check |
| `push` | `main` | Full gates (no PR-body issue check) |

Issue-linked PRs are the intended path for Project 5 Todo work (#12, #16, #17, research #9, design #13). Use the [PR template](../.github/PULL_REQUEST_TEMPLATE.md) with `Fixes #N` / `Closes #N` / `Related: #N`.

## Jobs

1. **`autoroute`** — asserts `vol_hard_max == 100` first (legacy “hard max 20” drift), installs `services/autoroute-adk/requirements.txt`, runs `bash scripts/autoroute_dev.sh`, then import smoke for clamps / sudden_freq / Hold refuse.
2. **`static_gates`** — `bash scripts/ci_static_gates.sh`: Hold/Manual in `public/index.html`, no obvious API-key patterns in HTML, `public/patch.json` `schemaVersion: 1`, clamp constants.
3. **`pr_issue_ref`** (PR only) — fails if title/body lack an issue ref (`#N` or `Fixes`/`Closes`/`Resolves`/`Related` `#N`).

## Local reproduction

```bash
bash scripts/ci_static_gates.sh
bash scripts/autoroute_dev.sh
```

Evidence package: [`.vv/ci/`](../.vv/ci/).

## Out of scope

- Heavy Firecrawl / link crawls
- Live GCP / Vertex / Vercel deploy
- Editing SEBoK plan files
