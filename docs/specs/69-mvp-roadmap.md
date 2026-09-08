# #69 — Durable MVP feature roadmap

## Status

`docs/mvp-roadmap.md` maps milestones M0–ship to issue numbers; living doc with closed-log convention.

## Goal

Keep a durable milestone → issue map for the web MVP ship path without relying on Project board UI alone.

## Prior art

Pair with `docs/mvp-closed-log.md` (#65/#68) and `docs/specs/README.md`; do not duplicate closed chronology in the roadmap table.

## Shipped on `main`

In-flight with Balanced PR6 / related docs PRs.

## Remaining scope

Update milestone rows only when ownership changes; closes go to the closed log.

## Wire fields

None.

## Clamps / safety

Public docs stay generic (no street addresses / PII).

## Acceptance tests

Roadmap links resolve; closed-log convention documents timeline-comment + `--backfill`.

## CI gate

Doc presence asserted by `tests/test_mvp_closed_log.py`.

## Risks / HW limits

Stale milestone rows if not updated when issues move.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/69
- `docs/mvp-roadmap.md`
