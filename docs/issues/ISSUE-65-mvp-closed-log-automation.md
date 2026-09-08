# #65 — Closed-issue log automation (duplicate)

Tracking: https://github.com/team-project-pikachu/IoT-ASP/issues/65
**Superseded by [#68](https://github.com/team-project-pikachu/IoT-ASP/issues/68).** Do not implement against #65.
See `docs/mvp-roadmap.md` and `docs/mvp-closed-log.md`.
# ISSUE-65 / #68 — Closed-issue → mvp-closed-log automation
**Issues:** https://github.com/team-project-pikachu/IoT-ASP/issues/65 (closed tracker) · https://github.com/team-project-pikachu/IoT-ASP/issues/68 (open logging goal)  
**Classification:** docs + workflow (Balanced PR6)  
**Status:** log seeded + CLI + Action present — **does not claim Actions can push main without bypass**
## Did
- `docs/mvp-closed-log.md` append-only format
- `scripts/mvp_closed_log_append.sh` idempotent local/CI helper
- `.github/workflows/mvp-closed-log.yml` — on `issues: [closed]` opens/updates PR branch `automation/mvp-closed-log` (or optional `MVP_CLOSED_LOG_PUSH_MAIN=1`)
- Tests: `tests/test_mvp_closed_log.py`
## Didn't
- Invent secrets for the workflow (uses `github.token`)
- Force-push main from automation by default
## Next
- Merge this stack; close `#68` when log+workflow accepted
- Owner may set repo variable `MVP_CLOSED_LOG_PUSH_MAIN=1` only with ruleset bypass
