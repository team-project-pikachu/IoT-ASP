# ISSUE-01 — M0 public Vercel hop blaster

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/1  
**Classification:** ship / stub iterate (Balanced)  
**Status:** implemented (shipped on main)  
**Spec:** `docs/specs/01-m0-public-blaster.md`

## Did

- `public/` single-file PWA + `vercel.json`
- Live URL: https://hop-ultrasonic-1digital-design.vercel.app/ (also in `public/README.txt`)
- Fleet (generic, no site PII): 3 phones — 2× iPhone 16 + 1× iPhone 14, each 1:1 over **iOS native Bluetooth A2DP** to its own Soundcore 2 (C1). No Web Bluetooth.
- Spec + static/e2e gates: `docs/specs/01-m0-public-blaster.md`
- Durable tracker note (this file) for Project 5 / closed-log independent of the board UI.

## Didn't

- Invent credentials or claim cloud/HW integrations live when gated.
- Auto-close the GitHub issue (human verifies).
- Invent continuous-ship secret values (#27 still owner-gated).
- Alter remaining "two phones" UI strings (owner election; fleet is three).

## Next / residual

- [ ] Optional: align remaining "two phones" UI copy when owner elects
- [ ] Continuous MVP ship via Actions once #27 secrets are set
- Live PROD Actions promo may still need secrets (#27)
- SSO/protection bypass optional

## Related (in-repo)

- Spec: `docs/specs/01-m0-public-blaster.md`
- Spec index: `docs/specs/README.md`
- Closed-log (when present on branch): `docs/mvp-closed-log.md` (#68)
- Roadmap (when present on branch): `docs/mvp-roadmap.md` (#69)

Note: Prefer **this** file as the single ISSUE-01 status record. Do not add a second `ISSUE-01-*.md`.
