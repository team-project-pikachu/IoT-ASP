# #61 — Wire live backend URLs for 3-phone fleet

## Status

UI affordance for backend patch/telemetry URLs landed with Balanced MVP docs; live URLs remain owner-gated.

## Goal

Make `BACKEND_TELEMETRY_URL` / patch URL discoverable and settable for the three-phone fleet without baking secrets into the static PWA.

## Prior art

Reuse existing `?patch=` / `?telemetry=` query params and `docs/api-contract.md` rather than inventing a second config channel.

## Shipped on `main`

Public PWA already accepts optional backend URL query params; this issue tracks wiring them for the field fleet.

## Remaining scope

Document operator procedure, confirm URLs against #60 deploy, and verify beacons in field lab (#62).

## Wire fields

Existing patch/telemetry URL query params only; no secret values in HTML.

## Clamps / safety

Names-only in page source; never embed API keys.

## Acceptance tests

With URLs set, phones poll patch and emit telemetry; with URLs unset, offline blaster still works.

## CI gate

Static HTML gates (no key patterns); live URL check is manual.

## Risks / HW limits

Mis-pointed URLs fail closed to local/static behavior.

## Sources

- https://github.com/team-project-pikachu/IoT-ASP/issues/61
- `docs/api-contract.md`
