# #63 — Main branch protection ruleset

## Status

**Done on main** for config/scripts/docs. Live ruleset application recorded via prior status report (ruleset id 22505825, enforcement=active on 2026-09-08). Residual: owner re-verify after intentional rule edits; keep JSON ↔ `ci.yml` job names in sync.

Evidence: `.vv/ci/branch-protection.md`

## Goal

Apply a main-branch ruleset so CI required checks gate merges without empty bypass actors unless explicitly elected.

## Prior art

Reuse `scripts/gh_protect_main.sh`, `docs/branch-protection.md`, and `.vv/ci/branch-protection.md`.

## Shipped on `main`

| Deliverable | Path |
|-------------|------|
| Ruleset JSON | `.github/rulesets/main-protection.json` |
| Apply script | `scripts/gh_protect_main.sh` / `make protect-main` |
| Context lock tests | `tests/test_ruleset_json.py` |
| Operator doc | `docs/branch-protection.md` |
| V&V evidence | `.vv/ci/branch-protection.md` |

## Remaining scope

- Owner re-run of verify commands after any intentional ruleset edit
- Do not invent new required contexts without updating both `ci.yml` and the JSON in the same PR

## Wire fields

None.

## Clamps / safety

Do not disable TLS, sandboxes, or trust checks to “make CI green.”

## Acceptance tests

- [x] Ruleset JSON + scripts + docs on main
- [x] pytest ruleset tests assert contexts match ci.yml job names
- [x] Prior live status report recorded (id 22505825, active)
- [ ] Owner re-verify GH013 / ruleset list after any future edit

## CI gate

Meta: this issue *is* the gate policy for other CI jobs. `pr_issue_ref` remains a required context once the ruleset is active.

## Risks / HW limits

Misconfigured bypass actors can silently weaken protection.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/63
- `docs/branch-protection.md`
- Issue comment on #63 (Balanced PR8 status, ruleset id 22505825)
