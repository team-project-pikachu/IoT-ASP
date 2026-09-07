# Carrier algorithms (EE first cut)

Band: **17–23 kHz** near-ultrasonic carriers over Web Audio → Bluetooth → Soundcore 2.  
Expect **BT codec + BassUp/DSP roll-off** (`SPEC.md`). Residential-safe default output ≤ ~8–12% Web Audio gain.

## Fleet topology

| Node | Hardware | Rooms | Vib channel bias | Status |
|------|----------|-------|------------------|--------|
| 1 | iPhone 16 ↔ Soundcore 2 | Room A | Acoustic (mic/spectrum) + optional accel | **Active** |
| 2 | iPhone 16 ↔ Soundcore 2 | Room B | Acoustic + optional accel | **Active** |
| 3 | Future iPhone (e.g. 14) **taped to a chair** | TBD | **Physical / structure-borne** (linear accel); chair frame → seat → floor | **Parked** |

Nodes 1–2 blast **incoherently** (independent per-tab RNG). Humans and ambient external sounds are in-scope interferers (details live in the private study repo).

Node 3 (parked): mechanical coupling to chair materials dominates free-handheld motion — prefer accel-triggered **pulse / shriek** algorithms when armed.

## Sensing / actuation classes

| Class | Band / nature | Practical web sensor | Actuation |
|-------|---------------|----------------------|-----------|
| Near-ultrasonic | 17–23 kHz | — (TX path) | Phone → BT → Soundcore 2 |
| Acoustic / audible external | ~20 Hz–20 kHz air path | Mic + spectrum | May gate/switch algos |
| Physical vibration | Broadband structure-borne | Linear accel / DeviceMotion | Chair/table/mount |
| **Infrasound (felt-not-heard)** | **&lt;20 Hz** | **LF accel energy only** (mic/BT **cannot** claim true infrasound) | Maps to pulse rate / duty / hop aggression |

### Infrasound honesty (iPhone web)

- Consumer BT speakers/mics **high-pass**; Safari cannot cleanly play or capture true infrasound.
- Proxy: **very-low-frequency linear accelerometer** energy (body/chair coupling) = practical “felt” channel.
- Dedicated infrasound mic / geophone = **parked** research (native hardware).

## Vibration → algorithm routing

| Detected class | Sensor | Default algorithm switch |
|----------------|--------|--------------------------|
| `physical` | `DeviceMotionEvent.acceleration` (or incl. gravity − ĝ) | Prefer **burst / shriek_chirp / am_gate** |
| `acoustic` | Mic analyser energy in 17–23 kHz (or broadband transient) | Prefer **am_gate / hop / shriek_sweep** |
| `infra_felt` | LF accel energy (≲20 Hz proxy via motion sample stream) | Prefer **`infra_mod`**: raise pulse rate / shriek duty / hop aggression |
| `none` / idle | — | Stay on selected manual mode (default **hop**) |

Debounce: ≥250–400 ms between vib-triggered switches. Thresholds tunable (`vib sensitivity`).

Chair-taped node 3: raise **physical + infra_felt** bias / lower acoustic weight so floor/chair thumps and LF sway rotate toward pulse/shriek/`infra_mod`.

## Algorithms

### 1. `hop` — incoherent frequency hop (default)
Continuous sine; each dwell picks uniform random f ∈ [f_lo, f_hi] via per-device RNG. Jump or short glide. Coverage over time, no shared seed across phones.

### 2. `am_gate` — AM / gated pulses
Carrier held near band center (or slow hop); gain gated on/off (pulse period ~50–200 ms, duty 20–50%). “Pulsating” character; lower continuous SPL.

### 3. `shriek_chirp` — short upward chirps
Linear/exponential sweep bursts (e.g. 17→22 kHz over 30–80 ms), silence gap, repeat. Keep gain low for residential courtesy.

### 4. `shriek_sweep` — slower band sweeps
Longer sweeps across 17–23 kHz (0.5–2 s), optional reverse. Stresses speaker FR and reveals roll-off.

### 5. `burst` — random tone bursts
Sparse random (f, duration ∈ 20–120 ms) packets with longer gaps. Temporal sparsity for courtesy while remaining detectable in spectrograms.

## Implementation notes (`public/index.html`)

**Public status (Lane A, 2026-09-07):** hop / pulse / shriek + vib auto-route **shipped** at https://hop-ultrasonic.vercel.app/ (SSO off). Fleet copy is generic (2×1:1 BT + optional chair node); no site PII in public HTML/README.

- Algo selector + optional vib auto-route (physical → pulse/shriek; acoustic → am_gate/hop).
- Safe default: `hop` + low `vol`.
- Recordings: MediaRecorder → local `.webm` + JSON sidecar → **private** study upload path (see local `study/` — gitignored; not on public default branch).

## Privacy

Ambient capture may include speech/external sounds. Raw archives and site protocol are **private** — never commit street addresses or recording URIs here.


## Physics priors (routing rationale)

Structure-borne vs air-borne vs infra_felt routing is grounded in linearized acoustic / Navier–Stokes–derived wave equations and seismo-acoustic coupling analogies — see [physics.md](physics.md). Gemini/ADK autoroute may use these as **constraints/priors** only ([adk-autoroute.md](adk-autoroute.md)).
