# ISSUE-34 — mdc_convert GEN_MARK guard

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/34  
**Classification:** ship / stub iterate (Balanced)  
**Status:** implemented (stack PR2) + regression coverage retained (stack PR5)

## Did

- `scripts/mdc_convert.py` — GEN_MARK refuse + nested `IoT-ASP-wt-*` exclude prefixes
- `tests/test_mdc_convert.py` — refuse / `--force` / long frontmatter / nested worktree skip
- `docs/mdc-conversion.md`
- `.gitignore` `/IoT-ASP-wt-*/`

## Didn't

- Invent credentials or claim cloud/HW integrations live when gated.
- Auto-close the GitHub issue (human verifies).

## Next

- Merge after CI green; overlaps historical PR #35 acceptance
