# Physics priors — linearized acoustics, Navier–Stokes, seismo-acoustic coupling

Public scientific tooling notes. **No site PII.** Priors inform vib→algorithm routing and Gemini/ADK prompts — **not** full CFD on-phone.

## Paths

| Path | Medium | Dominant sensing (web fleet) | Routing bias |
|------|--------|------------------------------|--------------|
| **Air-borne** | Compressible air; acoustic wave equation | Mic / spectrum energy | `acoustic` → `am_gate` / `hop` / `shriek_sweep` |
| **Structure-borne** | Elastic solid / frame / chair | Linear accel (`DeviceMotion`) | `physical` → `burst` / `shriek_chirp` / `am_gate` |
| **Felt infrasound proxy** | &lt;20 Hz body/chair coupling | LF accel energy (mic/BT **cannot** claim true infrasound) | `infra_felt` → `infra_mod` (pulse/shriek duty ↑) |
| **Optional LF TX 10–20 Hz** | Air / structure if transducer allows | Web Audio oscillator when **armed** + `lfDriveCapable` | Telemetry `band=10-20`; **na** on most BT speakers ([DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) **C6**) |

## Linearized acoustic / NS-derived wave equation (prior)

From compressible Navier–Stokes, under small perturbations about a quiescent or slowly varying mean flow, one recovers a **linearized acoustic wave equation** for pressure perturbation \(p'\):

\[
\frac{1}{c_0^2}\partial_t^2 p' - \nabla^2 p' = \mathcal{S}
\]

where \(c_0\) is ambient sound speed and \(\mathcal{S}\) collects aeroacoustic / vibration sources (Lighthill-type source terms in full aeroacoustics). For **structure-borne** paths, coupling enters through boundary motion (normal velocity / acceleration of surfaces) rather than free-field air sources alone.

**IoT-ASP implication:** near-ultrasonic TX (17–23 kHz) is an intentional air-borne carrier; residential floors/chairs inject **structure-borne** and **LF felt** channels that the vib classifier should prefer over mic-only when accel energy dominates.

## Earthquake / seismo-acoustic coupling (prior)

Earthquakes and induced seismicity radiate **seismic** (elastic) and **acoustic/infrasonic** energy. Seismo-acoustic literature studies how ground motion couples into air (and vice versa via DAS/hydroacoustics). For a townhome instrument, we treat this as an analogy for **building vibration → air/structure coupling**, not as earthquake early-warning.

**IoT-ASP implication:** when LF accel (“felt”) rises without in-band mic energy, prefer pulse/shriek/`infra_mod` rather than continuous hop — consistent with structure-coupled disturbance rather than air-borne interferer.

## Honesty limits

- Safari + BT speaker/mic: **no** faithful infrasound TX/RX; LF accel is a **proxy**.
- Optional **10–20 Hz** Web Audio drive is **hardware-gated**: Soundcore/A2DP usually **na**; phone speaker may pass enough energy to matter. Never claim calibrated infrasound SPL from the PWA alone.
- Fleet power is **continuous 120 V AC** ([power-fleet.md](power-fleet.md)) — physics priors are not battery-duty-cycled.
- ADK/Gemini may **cite** these equations as constraints/priors for pitch/pulse/shriek recommendations.
- Do **not** claim solving full Navier–Stokes or CFD on the device.

## Literature (cite in autoroute priors — no fabricated IDs)

| ID | Role for IoT-ASP |
|----|------------------|
| [arXiv:2307.01775](https://arxiv.org/abs/2307.01775) | Aeroacoustics / quiescent linearized wave equation |
| [arXiv:2509.17986](https://arxiv.org/abs/2509.17986) | Linearized compressible Navier–Stokes (cavity aeroacoustics) |
| [arXiv:2211.03647](https://arxiv.org/abs/2211.03647) | Seismo-acoustic nuisance / coupling analogy |
| [DOI 10.1121/1.5063819](https://doi.org/10.1121/1.5063819) | VHFS/US human effects Part I (exposure ethics) |
| [DOI 10.1121/10.0003509](https://doi.org/10.1121/10.0003509) | Infrasound annoyance / perception (&lt;20 Hz felt context) |
| [PMID 27780424](https://pubmed.ncbi.nlm.nih.gov/27780424/) | Human–seat coupling (structure-borne chair path) |

Full pull notes: [reference/LITERATURE.md](../reference/LITERATURE.md) § Navier–Stokes / aeroacoustics / seismo-acoustic.  
Worker weights + tool: `services/autoroute-adk/iot_asp_autoroute/priors.py`. Algorithms table: [algorithms.md](algorithms.md).
