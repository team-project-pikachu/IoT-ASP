# #5 — Acoustic vib response (native mic / spectrum energy)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/5 · Milestone: [iOS / iPhone](https://github.com/team-project-pikachu/IoT-ASP/milestone/10)

## Status

**Implemented on this branch (native).** `AcousticVibChannel` uses a rolling median (~1 s at 50 Hz) and flags `acousticBurst` when energy − median ≥ 12 dB. Prefers `micDiff` when present so self-TX is less likely to fire. Not full AEC (#25).

## Goal

Respond to air-path energy bursts in the 17–23 kHz hop band (Soundcore / room). Couples to #141 metering.

## Prior art

Web analyser mean 17–23 kHz in `public/index.html`; spec 04-06 remaining burst detector; `mic_diff.py` α=0.85. **Build** native channel; do not vendor AudioKit.

## Shipped on `main`

Web `acousticEnergy > -55 dB` class only. No native burst-vs-median.

## Remaining scope

On-device tone burst. FFT-true `bandEnergyUs` in the engine tap (#141 remaining).

## Wire fields

`vibClass=acoustic`, `micEnergy`, `micDiff`, `bandEnergyUs`. No schemaVersion bump.

## Clamps / safety

Disarmed → `.none`. Burst margin 12 dB. Hold / Manual still wins at alarm. No audio upload.

## Acceptance tests

Median of [-10,-20,-30]==-20; quiet then -20 dB → burst; micDiff -80 suppresses burst vs loud energy; disarmed none.

## CI gate

IoTASPSmoke + `tests/test_acoustic_vib.py`.

## Risks / HW limits

Phone mic + A2DP roll-off; `micEnergy` is relative. Self-TX without micDiff will false-trigger.

## Sources

Issue #5, `docs/specs/04-06-vibration-channels.md`, `docs/specs/141-ultrasonic-mic.md`, `docs/api-contract.md` micDiff row.
