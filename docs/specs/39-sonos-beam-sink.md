# #39 — Sonos Beam Gen 2 sink

## Status

Parked research with an unsigned native AirPlay route-picker shell.

## Goal

Evaluate a third fleet node using a Sonos Beam Gen 2 without treating AirPlay as C1-compliant carrier TX.

## Prior art

Reuse the repository ADR and shell in `docs/sonos-beam.md` and `native/ios-sonos-shell/`. AirPlay is an explicit research exception; the Soundcore path remains native iOS Bluetooth A2DP.

## Shipped on `main`

No Sonos control path is shipped on `main`.

## Remaining scope

Validate routing on owned hardware, measure latency/roll-off, and decide whether the parked exception should graduate.

## Wire fields

No new contract fields. Existing `route` and node identity telemetry remain descriptive.

## Clamps / safety

C1 remains authoritative: AirPlay does not satisfy the carrier-path requirement. Hold / Manual still wins.

## Acceptance tests

The native UI labels the Sonos route as a parked exception, and changing the selected sink reapplies the audio-session policy.

## CI gate

Swift package tests and static project checks; signed device validation remains manual.

## Risks / HW limits

AirPlay latency and Beam DSP are hardware/network dependent and are not characterized by this stub.

## Sources

- `docs/sonos-beam.md`
- https://developer.apple.com/documentation/avkit/avroutepickerview
