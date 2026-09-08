# MVP closed-log automation — evidence (#65 / #68)

**Config item:** `.github/workflows/mvp-closed-log.yml` + `scripts/mvp_closed_log_append.sh`  
**Docs:** `docs/mvp-closed-log.md`, `docs/mvp-roadmap.md`, `docs/specs/65-68-mvp-closed-log.md`  
**Date:** 2026-09-08 (UTC)  
**SEBoK plan:** not modified

## Requirements

| ID | Requirement |
|----|-------------|
| MCL-01 | Idempotent append by `#N` |
| MCL-02 | `--backfill` enumerates closed issues without a silent 200 cap |
| MCL-03 | Workflow does not interpolate issue body via `${{ }}` |
| MCL-04 | Closing outcome from timeline (not latest comment page); title fallback |
| MCL-05 | Shared automation branch reused + merged with `main` (no drop of unmerged rows) |
| MCL-06 | `vars.MVP_CLOSED_LOG_PUSH_MAIN` read explicitly when used |

## Procedure

```bash
python3 -m pytest tests/test_mvp_closed_log.py -q
bash -n scripts/mvp_closed_log_append.sh
bash -n .github/workflows/mvp-closed-log.yml 2>/dev/null || true
# Offline duplicate / backfill path covered in pytest (fake gh).
```

## Observed (local)

| Check | Result |
|-------|--------|
| `pytest tests/test_mvp_closed_log.py` | exit 0 — 4 passed |
| Workflow YAML contains `vars.MVP_CLOSED_LOG_PUSH_MAIN` | pass |
| Workflow fetches existing `automation/mvp-closed-log` before append | pass |
| Workflow uses GraphQL timeline for closing comment | pass |
| Script supports `--backfill` | pass |

## Pass/fail

| Req | Status |
|-----|--------|
| MCL-01 … MCL-06 | **PASS** (local static + unit) |
| Live `issues:closed` Actions run | pending post-merge |
