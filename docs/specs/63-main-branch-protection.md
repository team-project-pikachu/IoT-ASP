# #63 — Main branch protection ruleset

## Status

Open infra MVP item; scripts/docs exist for applying required checks.

## Goal

Apply a main-branch ruleset so CI required checks gate merges without empty bypass actors unless explicitly elected.

## Prior art

Reuse `scripts/gh_protect_main.sh`, `docs/branch-protection.md`, and `.vv/ci/branch-protection.md`.

## Shipped on `main`

Protection helper scripts and docs; live ruleset application is owner-gated.

## Remaining scope

Owner election of required contexts; evidence package update after apply.

## Wire fields

None.

## Clamps / safety

Do not disable TLS, sandboxes, or trust checks to “make CI green.”

## Acceptance tests

Ruleset JSON / `gh` view shows required checks; unprotected push to main is denied.

## CI gate

Meta: this issue *is* the gate policy for other CI jobs.

## Risks / HW limits

Misconfigured bypass actors can silently weaken protection.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/63
- `docs/branch-protection.md`
