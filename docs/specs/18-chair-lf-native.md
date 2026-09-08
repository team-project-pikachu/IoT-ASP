# #18 — Node-3 chair-taped LF accel proxy (native)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/18 · Milestone: [iOS / iPhone](https://github.com/team-project-pikachu/IoT-ASP/milestone/10)

## Status

**Implemented on this branch (native proxy).** `LfAccelProxy` + `ChairNodeProfile`. Backend `infra_felt` priors already shipped. This does **not** deploy a physical chair node.

## Goal

Node 3 chair-taped prefers physical/structure-borne. Infrasound is a **felt proxy** via LF accel, not capture.

## Prior art

Spec `18-node3-chair-infrasound.md`; web `lfMag` EMA; `priors.infra_felt`. **Build** native IIR proxy; no geophone.

## Shipped on `main`

Backend priors + web crude lfMag. No native chair profile.

## Remaining scope

Tape a real phone to a chair (pilot). Better 0.5–20 Hz biquad vs this two one-pole sketch. LF TX still `lfDriveCapable=false`.

## Wire fields

`vibClass=infra_felt`, `lfEnergy`, `materialPreset=chair`. No schemaVersion bump. `band` stays `17-23k` unless lfDriveCapable.

## Clamps / safety

Thumps (high absA) are **physical**, not infra_felt. Honesty string required. No CFD/infrasound-capture claims.

## Acceptance tests

Chair arming physical-only; honesty contains “felt proxy”; slow sway can mark infra_felt; 1.5 g thump is not infra_felt.

## CI gate

IoTASPSmoke + `tests/test_lf_accel_proxy.py`.

## Risks / HW limits

True <20 Hz acoustic is out of reach. DeviceMotion ~60 Hz aliases thumps.

## Sources

Issue #18, `docs/specs/18-node3-chair-infrasound.md`, `docs/physics.md`.
