# Branch protection evidence — main-protection ruleset

**Config item:** `.github/rulesets/main-protection.json` + `scripts/gh_protect_main.sh`
**Docs:** `docs/branch-protection.md`
**Issue:** #63
**Date:** 2026-09-11 (UTC) closeout refresh

## Status on main

- Ruleset JSON, `scripts/gh_protect_main.sh`, `tests/test_ruleset_json.py`, and `docs/branch-protection.md` are already on `main`.
- CI keeps JSON contexts in lock-step with `ci.yml` job names (minus documented allowlist).
- Prior Balanced PR8 (#76) status report (issue comment on #63, 2026-09-08): live ruleset id **22505825**, `enforcement=active` via report-only `scripts/gh_protect_main_status.sh`.
- This session does **not** re-apply or mutate the ruleset (no admin mutation from the queue worker). Residual owner work is re-verify after any intentional rule edit (`make protect-main` / UI import) and keep `ci.yml` job names synchronized.

| Req | Check | Result |
|-----|-------|--------|
| RS-01…RS-04 | `python3 -m pytest tests/test_ruleset_json.py -q` (JSON shape, `~DEFAULT_BRANCH`, enforcement active in file, required contexts == ci.yml job names) | exit 0 on main (CI) |
| RS-05 | Live ruleset present with enforcement=active; direct push refused with GH013; `allow_auto_merge` / `delete_branch_on_merge` as configured | **Recorded from #76 status report** (id 22505825, active). Owner re-verify after any ruleset edit. |

## Invariants preserved

- No wire/schema change; no secrets; no product toggles.
- `vol_hard_max=100`, Hold/Manual freeze, C1 A2DP-only untouched.
- Empty bypass actors remain the source-of-truth policy in the JSON unless the owner explicitly elects otherwise.

## Out of scope this PR

- Setting Vercel Actions secret *values* (#27)
- Mutating the live ruleset from this worker
- #64 matrix pass rows (requires real evidence packages, not invented)
