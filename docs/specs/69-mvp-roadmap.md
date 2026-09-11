# #69 — Durable MVP feature roadmap

## Status

**Done on main.** Canonical plan is `docs/roadmap.md` (OS/product surface milestones). Legacy `docs/mvp-roadmap.md` remains as a pointer so old links resolve.

Evidence: [`.vv/69/mvp-roadmap-closeout.md`](../../.vv/69/mvp-roadmap-closeout.md).

## Goal

Keep a durable milestone → issue map for the web MVP ship path without relying on Project board UI alone.

## Prior art

Pair with `docs/mvp-closed-log.md` (#65/#68) and `docs/specs/README.md`; do not duplicate closed chronology in the roadmap table.

## Shipped on `main`

| Deliverable | Location |
|-------------|----------|
| Canonical OS/surface roadmap | `docs/roadmap.md` |
| Legacy M0–M9 pointer | `docs/mvp-roadmap.md` |
| Closed-issue audit trail | `docs/mvp-closed-log.md` + append script |
| Specs index | `docs/specs/README.md` |

## Remaining scope

None for acceptance. Update milestone ownership only when issues move; closes go to the closed log.

## Wire fields

None.

## Clamps / safety

Public docs stay generic (no street addresses / PII).

## Acceptance tests

- [x] Roadmap links resolve
- [x] Parked vs active called out
- [x] C1/C2 constraints noted
- [x] Closed-log convention documented

## CI gate

Doc presence asserted by `tests/test_mvp_closed_log.py`.

## Risks / HW limits

Stale milestone rows if not updated when issues move (process, not code).

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/69
- `docs/roadmap.md`
- `docs/mvp-roadmap.md`
