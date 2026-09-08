# #25 — Native AEC / LF leftover honesty

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/25

## Status

**Related implementation only — do not close #25.** Full AEC and true LF mic remain HW-limited. Backend `mic_diff.py` already shipped.

## Goal

Native companion honesty: measurement mode, no voice-processing I/O, same α=0.85.

## Prior art

`mic_diff.py`, spec 25, #141 measurement mode. **Build** honesty report; do not claim full AEC.

## Shipped on `main`

Backend helpers.

## Remaining scope

True AEC / LF mic / LF TX still hardware-limited.

## Wire fields

None new. `micDiff` already in contract.

## Clamps / safety

Do not block hop redeploys. fullAEC and lfMic stay false.

## Acceptance tests

`fullAEC==false`, `lfMic==false`, α==0.85.

## CI gate

IoTASPSmoke + `tests/test_native_aec_honesty.py`.

## Risks / HW limits

Same four leftovers as `hw_limits_report()`.

## Sources

Issue #25, `docs/specs/25-hw-limited-lf-aec-micdiff.md`.
