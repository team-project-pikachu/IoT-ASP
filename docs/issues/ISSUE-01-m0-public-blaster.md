# ISSUE-01 — M0: Public Vercel hop blaster

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/1  
Milestone: M0 — Public web blaster  
Spec: `docs/specs/01-m0-public-blaster.md`

## Status (queue worker 2026-09-08)

**Shipped on main** (static PWA + telemetry enrichment + watchdog + max-entropy seeds + static/e2e gates).

- Live URL: https://hop-ultrasonic-1digital-design.vercel.app/
- Source mirror: `public/` (single-file index.html + patch.json mock)
- Fleet (generic, no site PII): 3 phones — 2× iPhone 16 + 1× iPhone 14, each 1:1 over **iOS native Bluetooth A2DP** to its own Soundcore 2 (C1). No Web Bluetooth.
- `public/README.txt` records Live URL + three-phone fleet.

## Did / Didn't (this slice)

**Did**
- Confirm live URL and fleet text already present in `public/README.txt` and the feature spec.
- Add this durable issue tracker note so Project 5 / closed-log has a repo-side record independent of the board UI.
- Preserve invariants: schemaVersion 1, vol_hard_max=100, Hold/Manual, no keys in public/.

**Didn't**
- Invent continuous-ship secret values (#27 still owner-gated).
- Change product runtime or claim Actions prod promo complete.
- Alter HTML copy that still says "two phones" in a few UI strings (owner decision; fleet is three).

## Acceptance residual

- [x] Live URL recorded
- [x] Three-phone fleet recorded (no PII)
- [ ] Optional: align remaining "two phones" UI copy when owner elects
- [ ] Continuous MVP ship via Actions once #27 secrets are set

## Related

- Spec index: `docs/specs/README.md`
- Closed-log: `docs/mvp-closed-log.md` (#68)
- Roadmap: `docs/mvp-roadmap.md` (#69)
