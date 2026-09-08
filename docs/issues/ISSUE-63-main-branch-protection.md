# ISSUE-63 — Apply main branch protection ruleset

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/63  
**Classification:** ops docs (Balanced PR8 status)  
**Status:** live ruleset **active** — residual is keep JSON ↔ CI job names in sync

## Did

- `.github/rulesets/main-protection.json` + `docs/branch-protection.md`
- `make protect-main` → `scripts/gh_protect_main.sh`
- `tests/test_ruleset_json.py` shape checks
- PR8: `scripts/gh_protect_main_status.sh` (report-only)
- Live check 2026-09-08: `main-protection` id **22505825**, `enforcement=active`

## Didn't

- Re-apply or mutate the ruleset from this session (already active)
- Add bypass actors / invent admin tokens

## Next

- Keep ruleset JSON and `ci.yml` job `name:`s locked via pytest
- Owner only re-runs `make protect-main` after intentional rule edits
