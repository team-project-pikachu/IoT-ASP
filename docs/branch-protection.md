# Branch protection for `main` — ruleset `main-protection`

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/27 (milestone M5)  
Owned files: `.github/rulesets/main-protection.json`, `scripts/gh_protect_main.sh`,
`tests/test_ruleset_json.py`, this doc. `make protect-main` wraps the script.

## Status

**Files shipped on this branch 2026-09-08; the ruleset is applied by the owner, not by CI.** The JSON is
the single source of truth and is both (a) importable through the GitHub UI and (b) a valid request
body for `POST /repos/team-project-pikachu/IoT-ASP/rulesets`. Applying it needs repository **admin**
and an authenticated `gh` — neither is available in a CI runner or a Claude session, so the apply step
is a one-time owner action (below). `tests/test_ruleset_json.py` keeps the JSON and `ci.yml` in lock-step.

## Why

- `main` is the only branch that deploys (`deploy.yml` fires on `workflow_run` of `CI — no breaking changes`
  for `main` — see `docs/specs/27-continuous-ship-dev-test-prod.md`). A direct push that skips CI can ship
  a broken `public/` or a clamp regression to the live app.
- The CI gates already exist (`docs/ci.md`); without protection they are advisory. The ruleset turns the five
  CI jobs into **required status checks** so a red job blocks the merge instead of just colouring the PR.
- Two writers (the owner's Cursor clone on the Mac and Claude Code branches) touch the same repo; a
  pull-request-only `main` gives one linear, reviewed history and no force-push accidents.
- Repo-level rulesets are readable by anyone with read access, exportable as JSON, and versioned here, so
  the protection is reviewable in a PR like any other config.

## What each rule does

The ruleset targets `~DEFAULT_BRANCH` (the special pattern for the repository default branch, i.e. `main`,
without hard-coding the name) with `enforcement: "active"` and an **empty** bypass list.

| Rule | Effect on `main` |
|------|------------------|
| `deletion` | Nobody can delete the branch (only bypass actors could, and there are none). |
| `non_fast_forward` | No force-pushes / history rewrites; every update must be a fast-forward of the current tip. |
| `pull_request` | Every change must arrive through a pull request. Parameters: `required_approving_review_count: 0` (no approval gate — see trade-off below); `dismiss_stale_reviews_on_push: true` (an approval, if any, is dropped when new commits change the diff); `require_code_owner_review: false` (no `CODEOWNERS` in this repo); `require_last_push_approval: false`; `required_review_thread_resolution: true` (all review conversations must be resolved before merge); `allowed_merge_methods: ["squash", "merge"]` (rebase-merge is disallowed so the merged tip is either a single squash commit or a real merge commit with the PR number in the subject). |
| `required_status_checks` | The PR's head must be green on all listed contexts. `strict_required_status_checks_policy: true` = "require branches to be up to date": the checks must have run against a head that already contains the current `main`. Auto-merge does **not** update the branch for you: when `main` moves, the PR shows *Update branch* and someone (or `gh pr update-branch`) must bring it up to date before the re-run can pass — only a merge queue removes that step. `do_not_enforce_on_create: false` = the rule also applies when the branch is created via the API. |

Required contexts — these are the `name:` strings of the jobs in `.github/workflows/ci.yml`
(`autoroute`, `static_gates`, `pr_issue_ref`, `tests`, `mdc_check`), which is exactly what GitHub reports as
the check name for a workflow job:

| Context | ci.yml job | Gate |
|---------|-----------|------|
| `autoroute dry-run + clamps` | `autoroute` | `vol_hard_max=100` drift gate, `scripts/autoroute_dev.sh`, import/Hold smoke |
| `HTML Hold + secrets + patch.json` | `static_gates` | `scripts/ci_static_gates.sh` |
| `PR must reference an issue` | `pr_issue_ref` | `#N` / `Fixes #N` in PR title or body (PR-only job) |
| `tests` | `tests` | `python -m pytest tests -q` |
| `mdc check` | `mdc_check` | `python3 scripts/mdc_convert.py --check` |

`tests/test_ruleset_json.py` asserts the context set equals the job-name set parsed from `ci.yml` with
PyYAML **minus an explicit non-required allowlist** (currently `{"e2e smoke"}`, informative only), so renaming
a job without updating the JSON (or vice versa) fails CI — a required context that no job produces would
otherwise leave PRs permanently un-mergeable, and a new job must be either required or allowlisted.

### Trade-off: `required_approving_review_count: 0`

The repository has a single maintainer. GitHub does not let a PR author approve their own PR, so any
count ≥ 1 would make solo PRs un-mergeable without a second account and would break PR auto-merge.
With `0`, the protection comes from the **five required checks** plus thread resolution, not from a human
approval. Raise the count to `1` the day a second maintainer joins (edit the JSON, re-run the script).

### Escape hatch (not enabled): admin bypass on pull requests

`bypass_actors` is `[]` on purpose: the ruleset applies to the owner too, so a red check cannot be
merged past. If an emergency path is ever needed, add the repository **admin role** (`RepositoryRole`
`actor_id` `5`) with `bypass_mode: "pull_request"` — admins may then bypass *only when merging a pull
request*, never for direct pushes or deletions:

```json
"bypass_actors": [
  { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request" }
]
```

(`RepositoryRole` base-role ids per the `integrations/terraform-provider-github` ruleset docs: `2` maintain,
`4` write, `5` admin. `bypass_mode: "always"` would also allow bypassing direct pushes and deletions and is
**not** recommended; `exempt` skips the audit entry as well.) Keep the JSON in git as the source of truth
and, after any UI edit, re-export and diff it — verify in particular that `bypass_actors` still matches.

## How to apply

Either path needs repo admin. The script path is idempotent (create or update in place).

### A. `gh api` script (preferred)

```bash
gh auth login                          # once; needs the repo scope and admin on the repo
bash scripts/gh_protect_main.sh        # or: make protect-main
# REPO=owner/name bash scripts/gh_protect_main.sh   # other repo
# DRY_RUN=1 bash scripts/gh_protect_main.sh         # validate JSON + print the plan, no network
```

What it does, in order:

1. Validates `.github/rulesets/main-protection.json` (required keys, `enforcement: active`) and reads `name`.
2. `gh auth status` (fails with a hint if not logged in).
3. `gh api repos/$REPO/rulesets --jq '… select(.name == "main-protection" and .source_type == "Repository") | .id'`.
4. Found → `gh api -X PUT repos/$REPO/rulesets/<id> --input <json>`; not found →
   `gh api -X POST repos/$REPO/rulesets --input <json>`.
5. Lists `gh api repos/$REPO/rulesets` (id, name, enforcement, source).
6. `gh api -X PATCH repos/$REPO -F allow_auto_merge=true -F delete_branch_on_merge=true`
   (repo-level settings: the **Enable auto-merge** button on PRs and automatic head-branch deletion).
7. Prints `OK gh_protect_main`.

No token is read by the script; `gh` supplies auth from its own store. Nothing is echoed except ids,
names and booleans.

### B. GitHub UI import

1. Open https://github.com/team-project-pikachu/IoT-ASP/settings/rules/new?target=branch&enforcement=disabled
   (or **Settings → Rules → Rulesets → New ruleset → Import a ruleset**).
2. Choose `.github/rulesets/main-protection.json` from a local checkout, review, **Create**.
3. The import lands with whatever enforcement the form shows; make sure **Enforcement status = Active**
   before saving (the linked URL pre-selects `disabled` so you can review first).
4. Bypass list is empty by design; add the admin `pull_request` bypass only if you accept the trade-off above.
5. Separately enable **Settings → General → Pull Requests → Allow auto-merge** and
   **Automatically delete head branches** (the script's step 6).

## How to verify

```bash
gh api repos/team-project-pikachu/IoT-ASP/rulesets                 # id, name, enforcement=active
gh api repos/team-project-pikachu/IoT-ASP/rulesets/<id> --jq '.rules[].type'
#   deletion / non_fast_forward / pull_request / required_status_checks
gh ruleset check main --repo team-project-pikachu/IoT-ASP           # rules that apply to the branch (current gh)
gh ruleset list --repo team-project-pikachu/IoT-ASP
gh api repos/team-project-pikachu/IoT-ASP --jq '{allow_auto_merge, delete_branch_on_merge}'
```

Negative check (from any clone with push rights): `git push origin HEAD:main` on a branch with an extra
commit must be refused with `GH013: Repository rule violations found` / *Changes must be made through a
pull request*. Do not try a force-push; the `non_fast_forward` rule refuses it the same way.

Local, offline: `python3 -m pytest tests/test_ruleset_json.py -q` (JSON shape, contexts == `ci.yml` job
names, script `bash -n` + `DRY_RUN=1`, this doc's sections).

## Auto-merge and the Cursor flow

- **Auto-merge**: once `allow_auto_merge` is on, a PR can be armed with `gh pr merge --auto --squash <n>`
  (or the button). GitHub then merges it automatically the moment all five required checks are green and
  every review thread is resolved — no human approval needed because the count is `0`. With
  `strict_required_status_checks_policy: true`, an out-of-date head is not mergeable: auto-merge waits, and
  the branch must be updated (*Update branch*, `gh pr update-branch`, or a merge queue) so the checks re-run
  on a head that contains the current `main`.
- **`PR must reference an issue`** is a required context and only runs on `pull_request` events; that is
  consistent because under this ruleset every change to `main` *is* a PR. Pushes to `main` (merges) still
  run the other four jobs on the merge commit, which is what `deploy.yml` listens for.
- **Cursor on the Mac clone** (`/Users/machine/apps/IoT-ASP`, usually ahead of `origin/main`): a direct
  `git push origin main` will now be **rejected**. Push to a topic branch instead (`git switch -c cursor/<topic>`
  → `git push -u origin HEAD`), open a PR with `Fixes #N` / `Related: #N` in the body (the template does
  this), let CI go green, then merge or `gh pr merge --auto --squash`. Squash keeps the Mac's many small
  commits out of `main` history; use a merge commit when the branch history matters.
- **Claude Code branches** (`claude/<topic>-<id>`) are already PR-only; nothing changes for them.
- **Delete-branch-on-merge** removes the head branch after merge; the local branch stays until you prune
  (`git fetch --prune`).
- **Emergency**: if a required check is structurally broken (e.g. a job renamed), fix `ci.yml` **and** the
  JSON in the same PR — the `tests` job will otherwise fail on `test_contexts_match_ci_job_names_exactly`,
  and the old context would stay required until the ruleset is updated. There is no bypass; that is the
  point. If truly stuck, an admin has two documented paths, both leaving an audit trail:
  1. **Disable, merge, re-enable** — Settings → Rules → Rulesets → `main-protection` → set **Enforcement
     status** to **Disabled**, merge the fixing PR, set it back to **Active** (or re-run
     `bash scripts/gh_protect_main.sh`, which PUTs `enforcement: "active"` from the JSON). Equivalent from
     the CLI: `gh api -X PUT repos/team-project-pikachu/IoT-ASP/rulesets/<id> --input <(jq '.enforcement="disabled"' .github/rulesets/main-protection.json)`.
  2. **Temporary admin bypass** — add the `RepositoryRole` `5` / `bypass_mode: "pull_request"` entry from the
     escape-hatch section, apply, merge, then remove it and re-apply.

  Do **not** plan on the **Evaluate** status — it is a GitHub Enterprise feature (dry-run with Rule Insights);
  on this repo's plan the enforcement picker offers only **Active** and **Disabled** (see *Plan availability*
  and Sources).

## Plan availability

Per GitHub docs *About rulesets*: rulesets are available in **public repositories on GitHub Free and
GitHub Free for organizations**, and in public and private repositories on GitHub Pro, GitHub Team and
GitHub Enterprise Cloud. `team-project-pikachu/IoT-ASP` is **public**, so no plan change is needed. (If the
repo were ever made private on a Free org plan, the ruleset would stop being enforced until the plan
changed — another reason to keep the repo public.) Push rulesets and organization-level rulesets are
Team/Enterprise features and are not used here.
Likewise the **Evaluate** enforcement status is Enterprise-only: the non-Enterprise *About rulesets* / *Creating rulesets for a repository* pages list only
**Active** and **Disabled**, and the REST docs mark `evaluate` as exclusive to GitHub Enterprise. The
only non-enforcing state available here is **Disabled**.

## Acceptance

| ID | Check | Where |
|----|-------|-------|
| RS-01 | `main-protection.json` parses; keys `name`, `target`, `enforcement`, `bypass_actors`, `conditions`, `rules`; `name == "main-protection"`, `target == "branch"`, `enforcement == "active"`, `conditions.ref_name.include == ["~DEFAULT_BRANCH"]`, `exclude == []`, `bypass_actors == []`; no server-assigned keys (`id`, `source`, `_links`, …) so the file imports cleanly | `tests/test_ruleset_json.py::test_json_loads_and_required_keys`, `::test_enforcement_active`, `::test_targets_default_branch_only`, `::test_no_bypass_actors_by_default` |
| RS-02 | Rule types == `{deletion, non_fast_forward, pull_request, required_status_checks}`; `pull_request` parameters exactly as in the table above; `required_status_checks` has `strict_required_status_checks_policy: true`, `do_not_enforce_on_create: false`; contexts are unique and **equal** the set of `jobs.*.name` parsed from `ci.yml` with PyYAML minus the non-required allowlist (`e2e smoke`); `pr_issue_ref` is `if: github.event_name == 'pull_request'` | `::test_rule_types`, `::test_pull_request_parameters`, `::test_required_status_checks_parameters`, `::test_contexts_match_ci_job_names_exactly`, `::test_pr_issue_ref_job_is_pr_only` |
| RS-03 | `scripts/gh_protect_main.sh`: bash shebang, `set -euo pipefail`, `REPO` default `team-project-pikachu/IoT-ASP`, `gh auth status`, PUT-or-POST with `--input`, PATCH `allow_auto_merge=true` + `delete_branch_on_merge=true`, prints `OK gh_protect_main`; `bash -n` passes; `DRY_RUN=1` exits 0 offline without `gh`; no token-shaped strings in script or doc | `::test_script_syntax_and_conventions`, `::test_script_dry_run_offline`, `::test_script_no_secret_values` |
| RS-04 | This doc has the sections Why / What each rule does / How to apply / How to verify / Auto-merge and the Cursor flow / Plan availability / Acceptance / Sources, the UI import URL, `gh ruleset check main`, the `RepositoryRole` bypass recipe and the Context7 source id; the emergency path says **Disabled** (never recommends the Enterprise-only `evaluate` status — every mention of `evaluate` carries the Enterprise caveat) | `::test_docs_sections`, `::test_docs_emergency_path_uses_disabled_not_evaluate` |
| RS-05 | Live (owner, once): `gh api repos/team-project-pikachu/IoT-ASP/rulesets` shows `main-protection` with `enforcement: active`; a direct push to `main` is refused with `GH013`; `allow_auto_merge` and `delete_branch_on_merge` are `true` | manual — record in `.vv/ci/` (integrator) |

CI gate: the `tests` job (`python -m pytest tests -q`) runs RS-01…RS-04 on every PR; `scripts/ci_static_gates.sh`
and `scripts/autoroute_dev.sh` are unaffected (no `public/` or backend change).

## Sources

- Context7 `/websites/github_en_rest` — *REST API endpoints for rules* (`POST /repos/{owner}/{repo}/rulesets`
  body: `name` required, `target` `branch|tag|push`, `enforcement` `disabled|active|evaluate` (`evaluate` is Enterprise-only per the docs,
  so `disabled` is the only non-enforcing value on this repo's plan); `bypass_actors`,
  `conditions.ref_name` with `~DEFAULT_BRANCH` / `~ALL`, `rules[]`; `PUT /repos/{owner}/{repo}/rulesets/{ruleset_id}`
  same body; `bypass_actors[].actor_type` ∈ `Integration | OrganizationAdmin | RepositoryRole | Team | DeployKey | User`,
  `bypass_mode` ∈ `always | pull_request | exempt`). https://docs.github.com/en/rest/repos/rules
- GitHub docs — *About rulesets* (plan availability; up to 75 rulesets per repo; anyone with read access can
  view rulesets; *Using ruleset enforcement statuses* lists only **Active** and **Disabled** on the non-Enterprise page)
  https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
- GitHub docs — *Creating rulesets for a repository → Using ruleset enforcement statuses*: non-Enterprise page
  lists **Active** / **Disabled**; the `enterprise-cloud@latest` variant adds **Evaluate** (Rule Insights)
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository ;
  https://docs.github.com/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository
- GitHub docs — *Managing rulesets for a repository → Importing a ruleset* (New ruleset ▸ Import a ruleset ▸
  JSON file ▸ Create)
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository
- GitHub docs — *Available rules for rulesets* (require a pull request before merging; dismiss stale approvals;
  require conversation resolution; allowed merge methods; require status checks / up-to-date branches)
  https://docs.github.com/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- Firecrawl developer index — `integrations/terraform-provider-github` `docs/resources/repository_ruleset.md`
  (`bypass_actors` `RepositoryRole` ids `maintain → 2`, `write → 4`, `admin → 5`; parameter names and defaults for `pull_request`: `allowed_merge_methods` ⊆ `merge|squash|rebase`,
  `dismiss_stale_reviews_on_push`, `require_code_owner_review`, `require_last_push_approval`,
  `required_approving_review_count` default 0, `required_review_thread_resolution`; `required_status_checks`:
  `strict_required_status_checks_policy`, `do_not_enforce_on_create`, `required_check.context`)
  https://github.com/integrations/terraform-provider-github/blob/main/docs/resources/repository_ruleset.md
- GitHub CLI manual — `gh ruleset check [<branch>]`, `gh ruleset list`, `gh ruleset view --web`
  https://cli.github.com/manual/gh_ruleset_check ; `gh api` `--input`, `-X`, `-F` typed fields, `--jq`
  https://cli.github.com/manual/gh_api
- Repo: `.github/workflows/ci.yml` (job `name:` values), `docs/ci.md`, `docs/specs/27-continuous-ship-dev-test-prod.md`,
  `Makefile` (`protect-main`), `README.md` (Main protection line), `.claude/rules/ci-and-workflows.md`, issue #27.
