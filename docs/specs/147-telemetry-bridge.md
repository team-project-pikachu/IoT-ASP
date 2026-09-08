# #147 — Native sensors → telemetry / patch contract

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/147

## Status

**Implemented on this branch.** `TelemetryBridge` encodes schemaVersion 1 JSON. Empty telemetry URL disables POST. Hold / Manual refuses patch apply. No API keys.

## Goal

Same contract as the web hop app (`docs/api-contract.md`).

## Prior art

Web `telemetryPayload()`; #61 BACKEND URLs; `clamps.validate_patch`. **Build** Swift Codable models; do not embed Vertex keys.

## Shipped on `main`

Web beacon only.

## Remaining scope

Live URL owner-gated. Native URLSession POST on-device.

## Wire fields

Required ★: schemaVersion, deviceId, ts, algo, suddenFreq. Optional axes/mic/vibClass/materialPreset/holdManual/power=ac120/band=17-23k.

## Clamps / safety

Hold refuses patch. Algo whitelist. Empty URL = no POST. No secrets in repo.

## Acceptance tests

Fixture JSON required keys; shouldPost("") false; hold refuses; evil algo refused; encode schemaVersion 1.

## CI gate

IoTASPSmoke + `tests/test_telemetry_bridge.py`.

## Risks / HW limits

Offline-safe by default. Do not invent OAuth client IDs.

## Sources

`docs/api-contract.md`, issue #147, #61.
