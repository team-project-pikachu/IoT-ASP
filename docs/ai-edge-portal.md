# AI Edge Portal — optional packaging (#23)

**Status:** Parked / docs-only. Not required for the Vercel + GCP ADK hybrid
autoroute MVP.

## Intent

Optional Google **AI Edge** / on-device inference portal for future edge
packaging (local models, offline prior scoring) alongside the phone blaster.
Does **not** replace Vertex Gemini Enterprise seats for continuous monitor +
patch authoring.

## Packaging checklist (when unparked)

- [ ] Choose runtime: AI Edge / LiteRT vs on-device Gemini Nano-class (document pick)
- [ ] Bundle offline prior scorer only — no Vertex keys in the edge package
- [ ] Keep `schemaVersion: 1` wire compatibility with cloud ADK patches
- [ ] Honor Hold / Manual freeze and `vol_hard_max=100` clamps
- [ ] No street addresses / site PII in on-device logs
- [ ] Gate behind feature flag; default off for public Vercel hop
- [ ] Evidence folder under `.vv/` only after hybrid ADK is production-stable

## Non-goals (now)

- No blocking public hop redeploys
- No force-install of edge SDKs into `services/autoroute-adk/` in this PR
- No changes to `public/index.html` for edge packaging

## When to schedule

Only after hybrid autoroute (`services/autoroute-adk/`) is stable in production.
Track as Project 5 issue **#23**.

## Related

- Issue **#23**
- [gemini-enterprise.md](gemini-enterprise.md)
- [adk-autoroute.md](adk-autoroute.md)
- [awesome-iot-asp.md](awesome-iot-asp.md)
