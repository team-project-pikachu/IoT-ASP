# #43 — Soundcore 2 manufacturer specifications

## Status

Documentation implemented; response above the published audio band remains explicitly unverified.

## Goal

Maintain a sourced hardware dossier that separates manufacturer facts from repository assumptions.

## Prior art

Consolidate existing notes into `docs/hardware/soundcore-specs.md` and keep `docs/hardware/soundcore-2.md` as the short entry point.

## Shipped on `main`

No canonical manufacturer dossier is shipped on `main`.

## Remaining scope

Add owned-unit measurements for codec, DSP, latency, and ultrasonic roll-off without replacing manufacturer claims.

## Wire fields

No new fields. Hardware capability and route tags remain descriptive.

## Clamps / safety

The 17–23 kHz software band does not imply flat speaker output; existing backend clamps remain unchanged.

## Acceptance tests

Every numerical manufacturer claim has a source and unverified behavior is labeled as such.

## CI gate

Documentation link and static policy checks.

## Risks / HW limits

Published nominal specifications cannot establish ultrasonic acoustic output.

## Sources

- `docs/hardware/soundcore-specs.md`
- `docs/hardware/soundcore-2.md`
