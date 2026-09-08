# #68 — MVP closed-issue log automation

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/68 · Labels: `enhancement` · Related: [#69](69-mvp-roadmap.md), `docs/mvp-closed-log.md`, ~~#65~~ (duplicate)

## Status

**Implemented in this PR.** Offline append script + Actions workflow that appends a single Markdown table row when an issue closes. Prefers PR branch `automation/mvp-closed-log` under main protection; optional `MVP_CLOSED_LOG_PUSH_MAIN=1`.

## Goal

Keep an append-only, body-free audit of closed Project 5 issues in `docs/mvp-closed-log.md`, runnable offline via `scripts/mvp_closed_log_append.sh` and optionally via `.github/workflows/mvp-closed-log.yml`, without inventing secrets or pasting issue bodies.

## Prior art

| What | Where | Decision |
|------|-------|----------|
| Continuous-ship workflow offline tests | `tests/test_deploy_workflow.py` | Mirror structure for closed-log YAML + append script |
| Issue metadata via `gh` | repo convention | Titles + labels + milestone only |
| Ruleset / PR-branch pattern | `docs/branch-protection.md`, deploy workflow | Reuse `automation/mvp-closed-log` tip instead of resetting to main |

## Shipped

| What | Where |
|------|-------|
| Append / backfill script (pipe-escaped cells; insert before `## Backfill` blank) | `scripts/mvp_closed_log_append.sh` |
| Actions workflow (reuse remote branch + rebase onto main; fail on stash/append errors) | `.github/workflows/mvp-closed-log.yml` |
| Seed log table | `docs/mvp-closed-log.md` |
| Offline tests | `tests/test_mvp_closed_log.py` |
| Evidence | `.vv/mvp/closed-log.md` |

## Remaining scope

- Owner enables workflow permissions / optional `MVP_CLOSED_LOG_PUSH_MAIN` only if bypass exists.
- Soft-notice when push is blocked by ruleset (operator runs script locally).

## Wire fields

None.

## Clamps / safety

- Never interpolate issue title/body into `run:` via `${{ }}` — only the numeric issue id.
- No secrets in the log row; no `op://` or token values in git.
- Pipe characters in titles/labels/milestones are escaped before Markdown table formatting.

## Acceptance tests

1. First append of a closed issue inserts a table row **inside** the Markdown table (before the blank line preceding `## Backfill`).
2. Second close while `automation/mvp-closed-log` remains open reuses the remote branch (rebase onto `main`) and accumulates rows — does not wipe prior rows.
3. Duplicate delivery for the same issue number is a no-op (`already logged`).
4. Titles containing `|` produce escaped cells (no extra table columns).
5. Failed append / stash conflict fails the job (non-zero), not a silent success.
6. `python3 -m pytest tests/test_mvp_closed_log.py -q` exits 0 offline.

## CI gate

`tests` job runs `tests/test_mvp_closed_log.py` (stdlib + PyYAML; no network for structure tests; `gh` mocked or skipped for live fetch).

## Risks / HW limits

- Ruleset may block bot push — documented soft notice + local script fallback.
- Concurrent closes serialize via workflow `concurrency.group: mvp-closed-log`.

## Sources

- GitHub issue #68; `docs/mvp-roadmap.md`; `.claude/rules/docs-and-specs.md`.
