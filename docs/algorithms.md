# Carrier algorithms (EE first cut)

**Default band:** **17–23 kHz** near-ultrasonic carriers over Web Audio → **iOS native Bluetooth A2DP** (system audio route / Control Center) → Soundcore 2.  
**Optional band:** **10–20 Hz** LF drive when Systems check sets `lfDriveCapable` **and** the user arms LF ([DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) **C6**). Most Soundcore/A2DP paths are **na** for 10–20 Hz; phone speaker may be usable. Telemetry tags `band=10-20` or `band=17-23k`.  
**Not** Web Bluetooth (**C1**, [iphone-bluetooth.md](iphone-bluetooth.md)).  
Expect **AAC/SBC + BassUp/DSP roll-off** on ultrasonic (`SPEC.md`). Default Web Audio out **100%** (**C4**); BT/hardware still limit SPL. Fleet on **continuous 120 V AC** (**C5**, [power-fleet.md](power-fleet.md)).  
Primary control: **suddenFreq → Gemini/ADK autorotate** ([autoroute.md](autoroute.md)); materials presets in [materials-engineering.md](materials-engineering.md).

## Fleet topology

| Node | Hardware | Rooms | Vib channel bias | Status |
|------|----------|-------|------------------|--------|
| 1 | iPhone 16 ↔ Soundcore 2 | Room A | Acoustic (mic/spectrum) + optional accel | **Active** |
| 2 | iPhone 16 ↔ Soundcore 2 | Room B | Acoustic + optional accel | **Active** |
| 3 | **Third iPhone 16** ↔ **Sonos Beam Gen 2** (AirPlay) and/or chair-taped sensing | TBD | Physical / AirPlay TX + structure-borne bias | **Research** (#39 / #18) |

Nodes 1–2 blast **incoherently** (independent per-tab RNG). Humans and ambient external sounds are in-scope interferers (details live in the private study repo).

Node 3 (parked): mechanical coupling to chair materials dominates free-handheld motion — prefer accel-triggered **pulse / shriek** algorithms when armed.

## Sensing / actuation classes

| Class | Band / nature | Practical web sensor | Actuation |
|-------|---------------|----------------------|-----------|
| Near-ultrasonic | 17–23 kHz | — (TX path) | Phone → **iOS A2DP** → Soundcore 2 |
| Acoustic / audible external | ~20 Hz–20 kHz air path | Mic + spectrum | May gate/switch algos |
| Physical vibration | Broadband structure-borne | Linear accel / DeviceMotion | Chair/table/mount |
| **Infrasound (felt-not-heard)** | **&lt;20 Hz** | **LF accel energy only** (mic/BT **cannot** claim true infrasound) | Maps to pulse rate / duty / hop aggression |

### Infrasound honesty (iPhone web)

- Consumer BT speakers/mics **high-pass**; Safari cannot cleanly play or capture true infrasound.
- Proxy: **very-low-frequency linear accelerometer** energy (body/chair coupling) = practical “felt” channel.
- Optional **10–20 Hz TX**: gated UI path only; fall back to ultrasonic when HW **na** (issue **#18** for full HW / Node-3).
- Dedicated infrasound mic / geophone = **parked** research (native hardware).

### Night volume (America/New_York)

- Window **22:00–07:00**: UI volume progresses **0 → 100%** in **0.5** glides/jumps (not a battery duty-cycle; see **C5**).

## Vibration → algorithm routing

| Detected class | Sensor | Default algorithm switch |
|----------------|--------|--------------------------|
| `physical` | `DeviceMotionEvent.acceleration` (or incl. gravity − ĝ) | Prefer **burst / shriek_chirp / am_gate** |
| `acoustic` | Mic analyser energy in 17–23 kHz (or broadband transient) | Prefer **am_gate / hop / shriek_sweep** |
| `infra_felt` | LF accel energy (≲20 Hz proxy via motion sample stream) | Prefer **`infra_mod`**: raise pulse rate / shriek duty / hop aggression |
| `none` / idle | — | Stay on selected manual mode (default **hop**) |

Debounce: ≥250–400 ms between vib-triggered switches. Thresholds tunable (`vib sensitivity`).

Chair-taped node 3: raise **physical + infra_felt** bias / lower acoustic weight so floor/chair thumps and LF sway rotate toward pulse/shriek/`infra_mod`.

## Environmental sound burst → extreme variance

**Bands (sensing):** energy under **20 Hz** (LF) and/or **above 17 kHz** (near-US up to Nyquist/23 kHz). Mid-band speech/music is **not** the primary trigger.

**Self-TX rejection (best-effort, not full AEC):**

```
micDiff_band = micEnergy_band − α · outLevel_band
```

- `micEnergy_*` — mic analyser mean dB in LF (1–20 Hz) or US (17–23 kHz)
- `outLevel_*` — output-bus analyser mean dB in the same band (our hop/shriek)
- `α` ≈ 0.85 (`OUT_ALPHA`); when TX is silent (`outLevel < −90 dB`), no subtraction
- `micDiff = max(micDiff_lf, micDiff_us)` (quantized 0.1 dB)
- Honesty: iOS Chrome lacks reliable AEC for this path; subtraction is output-aware heuristic

**Detection:** rolling EMA baseline of `micDiff`; onset when `micDiff − baseline > BURST_ONSET_DB` (~9 dB). Telemetry `bandBurst` = `lf` | `us` | `both`.

**Response (sustained):** while `micDiff` stays hot (above release hysteresis), keep **extreme** mode: shriek family (`shriek_chirp` / `shriek_sweep` / `burst`) + aggressive dwell / vol (0.5-step, night ≤ `nightTargetVol`) / seed jitter within clamps. Exit after **~2.5 s** quiet. **Hold/Manual** freezes and clears extreme.

### Impulse → blast volume (alarm reactivity)

Quick impulses are sharper than the EMA burst onset and react **like a security alarm** (not a soft fade):

| `alarmState` | Meaning |
|--------------|---------|
| `armed` | Listening (`suddenAuto`); no active blast |
| `triggered` | Impulse onset; blast vol engaged immediately |
| `sustaining` | Impulse train / still-hot; blast vol + extreme/shriek/mirrors held |
| `cleared` | Quiet hysteresis satisfied; brief latch then return to `armed` |
| `off` | `suddenAuto` disabled |

**Impulse detectors:** (1) micDiff **sample-to-sample rise** &gt; `IMPULSE_RISE_DB` (~11 dB) or **peak vs EMA** &gt; `IMPULSE_PEAK_DB` (~14 dB); (2) accel **rise vs EMA** &gt; `IMPULSE_ACCEL_RISE` (scaled by vib sensitivity); (3) environmental `soundBurst` onset also enters the alarm path for fast reaction.

**Blast volume:** jump UI vol toward `VOL_PATCH_MAX` (100) in **0.5** quanta, capped by night `nightTargetVol` when active. **Hold / Manual** refuses blast, clears `impulse`/`volBlast`, and forces `alarmState=cleared`. Sustain while the impulse latch (~700 ms) or burst still-hot continues; clear only after **~2.5 s** quiet (`BURST_QUIET_MS`) — same hysteresis family as extreme exit.

**TX align:** default response band **17–23 kHz**; if `bandBurst` is `lf`/`both` **and** `lfDriveCapable`, may arm **10–20 Hz**. Continuous mic while armed/Signal on.

Wire fields: `soundBurst`, `extremeActive`, `impulse`, `volBlast`, `alarmState`, `micEnergy`, `outLevel`, `micDiff` / `micNet`, `bandBurst`. Evidence: `.vv/burst-shriek.md`. Related: #44 #45 #25 #42.

## Impulse → blast / alarm reactivity

**Web + native (issues #42 / #44 / #45; duplicates #46/#47/#50/#51; native #41).** Security-alarm style — not a gentle ramp.

| State | Meaning |
|-------|---------|
| `armed` | Sensors live; waiting for onset |
| `triggered` | First short-duration impulse (accel spike and/or `micDiff` onset with short rise time) |
| `sustaining` | Impulse train / hot micDiff continues; keep blast |
| `cleared` | Quiet hysteresis met (~**2.5 s**); remains observable until the next impulse retriggers |

**Impulse definition:** short rise (≲120 ms) where either (a) `|a|` jumps ≥ onset above EMA baseline, or (b) `micDiff` jumps ≥ ~9 dB above EMA baseline (same family as environmental burst).

**Blast:** set `volBlast=true`, jump UI `vol` toward **100** / `VOL_PATCH_MAX` (night window may cap via `nightTargetVol`; 0.5-step glide only when escalating from quiet under night rules). Prefer extreme / shriek / contour-mirror family while blasting. Hold / Manual disarm → `cleared`, freeze remote + blast (`holdManual` wins).

**Telemetry (additive, schemaVersion 1):** `impulse` (bool, latched through the next heartbeat), `volBlast` (bool), `alarmState` ∈ `armed`|`triggered`|`sustaining`|`cleared`.

**Surfaces:** Web DeviceMotion+mic (`public/index.html`); native iPhone+Watch [`native/IoTASP/`](../native/IoTASP/) (`Shared/Alarm/AlarmStateMachine.swift`). SensorKit not on web (#9).

**Intense vib:** treat **10–20 Hz** as intense vibrations band for TX gate and/or sensing priority (`infra_felt` / LF). Log **1–100 Hz** accel+gyro on native paths.


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

### 6. `cry_mirror` — infant-cry contour mirror (generative)
**Not a recording.** Band-mapped Web Audio synthesis that mirrors temporal/spectral *contours* of a baby wail/cry: irregular pitch glides (rise→peak→sob fall), sob-like AM tremolo, inhale-like gaps. Carrier stays within `fMin`/`fMax` (US or LF). UI alias: `cry`.

### 7. `siren_mirror` — ambulance-siren contour mirror (generative)
**Not a recording.** Alternates (a) two-tone hi/lo steps and (b) rising/falling triangular sweeps across the TX band. UI alias: `siren`.

### 8. `death_metal_mirror` — death-metal stylistic contour mirror (generative)
**Not a copyrighted track.** Harsh saw/square carrier, blast-beat-like rapid AM/tremolo gates, low detuned drone + intermittent higher “shriek” hops within band. Wire alias `metal_mirror` / UI `metal` → `death_metal_mirror`.

Extreme / `soundBurst` (LF &lt;20 Hz or US &gt;17 kHz `micDiff`) rotates among shriek family **and** these three contour-mirrors. Hold / Manual still freezes remote patches; night NY volume curve and BT honesty unchanged.

## Implementation notes (`public/index.html`)

**Public status (Lane A, 2026-09-07):** hop / pulse / shriek + vib auto-route **shipped** at https://hop-ultrasonic.vercel.app/ (SSO off). Contour-mirrors + extreme micDiff burst rotation added 2026-09-08. Fleet copy is generic (2×1:1 BT + optional chair node); no site PII in public HTML/README.

- Algo selector + optional vib auto-route (physical → pulse/shriek; acoustic → am_gate/hop) + contour-mirror buttons.
- Safe default: `hop` + low `vol`.
- Recordings: MediaRecorder → local `.webm` + JSON sidecar → **private** study upload path (see local `study/` — gitignored; not on public default branch).

## Privacy

Ambient capture may include speech/external sounds. Raw archives and site protocol are **private** — never commit street addresses or recording URIs here.


## Physics priors (routing rationale)

Structure-borne vs air-borne vs infra_felt routing is grounded in linearized acoustic / Navier–Stokes–derived wave equations and seismo-acoustic coupling analogies — see [physics.md](physics.md).  

**Worker weights:** `services/autoroute-adk/iot_asp_autoroute/priors.py` (`VIB_ALGO_WEIGHTS`, material channel bias, LF gate). Gemini/ADK must call tool `seismo_acoustic_priors` and treat returned equations/cites as **constraints/priors** only ([adk-autoroute.md](adk-autoroute.md)). Evidence: `.vv/16/`.
