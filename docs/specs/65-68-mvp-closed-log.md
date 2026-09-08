# #65 / #68 — Closed-issue MVP log automation

## Status

Implemented on Balanced / queue branches: seed log, CLI append + `--backfill`, Actions workflow with PR-branch push path.

## Goal

When a GitHub issue closes, append one durable line to `docs/mvp-closed-log.md` (idempotent by `#N`) so the roadmap has an audit trail outside Projects UI.

## Prior art

CLI-first (`gh`), matching `scripts/gh_*.sh`. Optional workflow uses `contents: write` and prefers `automation/mvp-closed-log` when main is protected. Repo variable `MVP_CLOSED_LOG_PUSH_MAIN=1` enables direct main push only when bypass exists.

## Shipped on `main`

Seed/log may land via these PRs; treat as in-flight until merged.

## Remaining scope

Land workflow + CLI; verify timeline-based closing comment; preserve shared automation branch across concurrent closes.

## Wire fields

None (docs-only audit trail).

## Clamps / safety

Never interpolate issue body into `run:` via `${{ }}`; sanitize pipes/newlines; no secrets in log lines.

## Acceptance tests

- Append once → second append skips (`already logged`).
- `--backfill` is paginated and idempotent.
- Offline `tests/test_mvp_closed_log.py` green.

## CI gate

`tests` job covers helper; workflow itself is event-driven.

## Risks / HW limits

Ruleset push denial; mitigated by automation PR branch (merged with `origin/main`, not recreated).

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/65
- https://github.com/team-project-pikachu/IoT-ASP/issues/68
- `scripts/mvp_closed_log_append.sh`, `.github/workflows/mvp-closed-log.yml`
