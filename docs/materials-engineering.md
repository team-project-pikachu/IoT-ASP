# Materials engineering — coupling priors

Public tooling. **No site addresses.** Priors for vib / sudden-freq → algorithm routing. Links: [physics.md](physics.md), issue **#16**.

## Coupling classes

| Path | Materials / setup | Dominant sensor | Autoroute bias |
|------|-------------------|-----------------|----------------|
| **Air-borne** | Room air; Soundcore cone → cabinet → free field | Mic / spectrum | Prefer `hop` / `am_gate` / `shriek_sweep` on external onsets |
| **Structure-borne** | Table, floor, chair frame, phone body contact | Linear accel | Prefer `pulse` / `shriek` / `burst` |
| **Speaker cabinet** | Plastic enclosure + dual drivers + BassUp DSP | Mic near cabinet + optional contact | Expect US roll-off; treat DSP as unknown filter |
| **Chair-taped node 3** (parked) | Phone taped to chair → seat → legs → floor | Accel-biased | Raise `physical` + `infra_felt` weight |

## Material presets (autoroute prior)

| Preset | Prefer channel | Prefer algos on suddenFreq |
|--------|----------------|----------------------------|
| `handheld` | acoustic + light physical | `hop`, `am_gate` |
| `table` | physical + acoustic | `am_gate`, `shriek_chirp` |
| `chair` | physical / infra_felt | `pulse`, `shriek`, `infra_mod` |
| `speaker` | acoustic (cabinet radiation) | `hop` retune / `shriek_sweep` |

Pass `materialPreset` in telemetry when known (no PII). ADK may use it as a soft prior with NS / seismo-acoustic constraints ([physics.md](physics.md)).

## Engineering notes

- **Impedance mismatch** at air↔solid boundaries reflects energy — structure-borne detection can dominate even when SPL is modest.
- **Damping** in foam/carpet reduces high-frequency structure paths; wood/metal chairs couple LF better → `infra_felt` proxy.
- Do **not** run FEM/CFD on-phone; Colab may later use vibroacoustic toolboxes (see [similar-projects.md](similar-projects.md)).
