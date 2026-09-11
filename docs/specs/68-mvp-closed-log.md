# #68 — Closed-issue logging for MVP roadmap

## Status

Implemented on `queue/#68-mvp-closed-log`: seed log, CLI append + paginated `--backfill`, optional Actions workflow.

## Goal

When a GitHub issue is closed, append a durable row to `docs/mvp-closed-log.md` so the MVP roadmap has an audit trail without relying on Projects UI alone.

## Prior art

CLI-first with `gh` (matches `scripts/gh_*.sh`). Optional Action on `issues: [closed]` with `contents: write`. Prefer unique automation PR branches when main is protected; repo variable `MVP_CLOSED_LOG_PUSH_MAIN=1` enables direct main push only when a bypass exists.

## Shipped on `main`

In-flight via PR #74 until merge.

## Remaining scope

Land workflow + CLI; verify push-denial soft path vs hard-fail on append/API errors.

## Wire fields

None (docs-only audit trail). Table columns: date, `#N`, title (≤80), labels, closer.

## Clamps / safety

Never copy issue bodies; no secrets in log lines; sanitize pipes in titles.

## Acceptance tests

- Single append is idempotent by `#N`.
- `--backfill` uses paginated `gh api --paginate` (not a silent 200 cap).
- Workflow fails on append/auth/parse errors; soft-notices only on push denial.

## CI gate

Optional workflow event-driven; offline tests recommended in follow-on (`tests/test_mvp_closed_log.py` on Balanced stack).

## Risks / HW limits

Ruleset push denial; mitigated by per-run automation branch + manual CLI path in `docs/mvp-closed-log.md`.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/68
- `scripts/mvp_closed_log_append.sh`, `.github/workflows/mvp-closed-log.yml`
