# #63 — Apply main branch protection

Tracking: https://github.com/team-project-pikachu/IoT-ASP/issues/63
See `docs/mvp-roadmap.md` for MVP pillar mapping.
# ISSUE-63 — Apply main branch protection ruleset
**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/63  
**Classification:** ops docs (Balanced stub)  
**Status:** artifact present — **apply remains owner-gated**
## Did
- `.github/rulesets/main-protection.json` + `docs/branch-protection.md`
- `make protect-main` → `scripts/gh_protect_main.sh`
- `tests/test_ruleset_json.py` shape checks
## Didn't
- Apply ruleset to the org/repo from this agent session
- Bypass actors / invent admin tokens
## Next
- Owner: `make protect-main` (or Settings → Rules import) when CI names are final
