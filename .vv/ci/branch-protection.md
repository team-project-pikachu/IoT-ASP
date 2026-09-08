# Branch protection evidence — main-protection ruleset

**Config item:** `.github/rulesets/main-protection.json` + `scripts/gh_protect_main.sh`
**Docs:** `docs/branch-protection.md`
**Date:** 2026-09-08 (UTC)
**Status:** ruleset not yet applied as of 2026-09-08 (issue #27) — the owner runs `make protect-main` once
(or imports the JSON at Settings → Rules → Rulesets → New ruleset → Import a ruleset).

| Req | Check | Result |
|-----|-------|--------|
| RS-01…RS-04 | `python3 -m pytest tests/test_ruleset_json.py -q` (JSON shape, `~DEFAULT_BRANCH`, enforcement active, required contexts == ci.yml job names) | exit 0 |
| RS-05 | `gh api repos/team-project-pikachu/IoT-ASP/rulesets` shows `main-protection` enforcement=active; direct push refused with GH013; `allow_auto_merge` / `delete_branch_on_merge` true | **pending owner run** |

After the owner applies it, record the ruleset id and the GH013 refusal line here.
