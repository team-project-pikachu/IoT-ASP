# CI evidence — no breaking changes (issue-linked PRs)

**Config item:** `.github/workflows/ci.yml` + `scripts/ci_static_gates.sh`  
**Docs:** `docs/ci.md`  
**Date:** 2026-09-08  
**SEBoK plan:** not modified

## Requirements

| ID | Requirement |
|----|-------------|
| CI-01 | Workflow on `pull_request` + `push` to `main` |
| CI-02 | `vol_hard_max=100` drift gate before/inside dry-run |
| CI-03 | `bash scripts/autoroute_dev.sh` must exit 0 |
| CI-04 | Clamp/schema + Hold refuse import smoke |
| CI-05 | `public/patch.json` has `schemaVersion: 1` |
| CI-06 | `public/index.html` retains Hold / Manual |
| CI-07 | No obvious API keys in public HTML |
| CI-08 | PR template + CI job require issue ref (`Fixes #N` / Related) |

## Procedure

```bash
bash scripts/ci_static_gates.sh
bash scripts/autoroute_dev.sh
```

On GitHub: open PR with `Fixes #N` → jobs `autoroute`, `static_gates`, `pr_issue_ref`.

## Observed (local pre-push)

| Check | Result |
|-------|--------|
| `ci_static_gates.sh` | exit 0 — Hold/Manual present; no key patterns; patch schemaVersion=1; vol_hard_max=100 |
| `autoroute_dev.sh` | exit 0 — `DRY-RUN OK`; `vol_hard_max=100.0`; Hold negatives OK |
| Workflow path | `.github/workflows/ci.yml` |
| PR template | `.github/PULL_REQUEST_TEMPLATE.md` |

## Pass/fail

| Req | Status |
|-----|--------|
| CI-01 … CI-08 | **PASS** (local gates); remote Actions green deferred to first PR/push |
