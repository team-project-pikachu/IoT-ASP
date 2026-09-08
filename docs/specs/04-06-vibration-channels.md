# #4 / #5 / #6 — Vibration channels: physical (DeviceMotion), acoustic (mic energy), material-dependent selection

Issues: https://github.com/team-project-pikachu/IoT-ASP/issues/4 · https://github.com/team-project-pikachu/IoT-ASP/issues/5 · https://github.com/team-project-pikachu/IoT-ASP/issues/6 · Milestone: M3 — Vibration response (physical + acoustic) · Labels: `enhancement`, `parked`
Related: [18-node3-chair-infrasound.md](18-node3-chair-infrasound.md) (chair node, `infra_felt`), [25-hw-limited-lf-aec-micdiff.md](25-hw-limited-lf-aec-micdiff.md) (`micDiff`, burst keys), [26-colab-live-gcs-features.md](26-colab-live-gcs-features.md) (`ax..gz`, `accelAxes`, `gyroAxes` features).

## Status

**Parked — partly shipped.** The three issues describe one feature with three faces. On `origin/main`
(`0625e91`) the phone already (a) listens to `devicemotion`, classifies `physical` / `infra_felt` from
accelerometer magnitude, (b) classifies `acoustic` from 17–23 kHz mic energy, (c) routes the algorithm
from the vib class when *Vib auto* is on, and (d) beacons `vibClass`, `absA`/`a`, `micEnergy`,
`vibThreshold`. The backend already carries the **material-dependent channel policy** as
`priors.MATERIAL_CHANNEL_BIAS` and applies it to the vib→algo weights. What is **not** shipped:
the #4 "debounced shake → force hop / reseed" action, the #5 "energy burst in hop band" detector as a
distinct event, the **material / arming UI** from #6 (`materialPreset` is documented on the wire but the
phone never emits it), and a phone-side channel-arming model (arm physical, acoustic, or both).
No implementation lands with this spec; it records what exists and fixes the remaining scope so the
issues can be unparked without re-deriving the design.

## Goal

1. **#4 physical:** a phone (handheld, on a table, or taped to a chair) responds to structure-borne
   vibration measured by `DeviceMotionEvent` — prefer `acceleration` (gravity excluded), fall back to
   `accelerationIncludingGravity` minus a gravity estimate — with a tunable threshold, ≥300 ms debounce,
   and an explicit *shake → force hop / reseed* action.
2. **#5 acoustic:** the same phone responds to air-path energy bursts in the 17–23 kHz hop band measured by
   the mic analyser (AEC/NS/AGC off), coupled to the Soundcore cone/cabinet and the Bluetooth path
   limits recorded in `SPEC.md`.
3. **#6 selection:** which channel(s) are armed depends on materials / setup, both as a backend prior
   (`MATERIAL_CHANNEL_BIAS`, shipped) and as an arming UI (`materialPreset` on the wire, not shipped):

   | Setup | Prefer | `materialPreset` |
   |-------|--------|------------------|
   | Phone-on-table / rigid mount | physical (accelerometer) | `table` |
   | BT speaker radiate / over-air | acoustic (mic/spectrum) | `speaker` |
   | Contact with Soundcore enclosure | physical + acoustic | `speaker` + both channels armed |
   | Handheld | acoustic-leaning | `handheld` |
   | Chair-taped node 3 (#18) | physical + `infra_felt` | `chair` |

## Shipped on `main`

Verified by reading `origin/main` @ `0625e91` (`git show origin/main:public/index.html`; backend files are
identical between `origin/main` and this branch — `git diff --stat origin/main HEAD -- services/` is empty).

| What | Where |
|------|-------|
| Vib state: `let vibAuto=false, vibClass="none", lastVibSwitch=0;` and `let accelMag=0, lfMag=0, acousticEnergy=-120;` | `public/index.html:487`, `:490` |
| *Vib off* / *Vib auto* buttons; `sens` slider `#vibSens` (`min=1 max=40 value=12`) | `public/index.html:318-319`, `:329` |
| `setVibAuto(on)` persists `hop.vibAuto`, calls `ensureMotion()` | `public/index.html:646-653` |
| `routeFromVib(cls)`: 300 ms debounce; `physical`/`infra_felt` → `shriek` (55 %) or `pulse`; `acoustic` → `pulse` or `hop` | `public/index.html:655-667` |
| `updateVibClass(cls)` → UI pill + `routeFromVib` | `public/index.html:669-674`; pill at `:241` |
| `ensureMotion()`: iOS `DeviceMotionEvent.requestPermission()` inside a user gesture (only from `setVibAuto`) | `public/index.html:751-757` |
| `devicemotion` handler: `e.acceleration \|\| e.accelerationIncludingGravity`; `accelMag` EMA (0.85/0.15); `lfMag` low-pass of gravity-magnitude deltas; `thr = vibSens/10`; `infra_felt` if `lfMag > 0.35·thr`, `physical` if `accelMag > thr`, release below `0.4·thr` to `acoustic`/`none` | `public/index.html:759-776` |
| Mic path: mean of `getFloatFrequencyData` bins between 17 000 and 23 000 Hz → `acousticEnergy` (dBFS); `acoustic` class when `> -55 dB` and not already physical/infra_felt | `public/index.html:1203-1212` |
| Beacon: `absA`/`a: accelMag`, `micEnergy: acousticEnergy`, `vibThreshold: vibSens/10`, `vibClass`, `holdManual` — **no `materialPreset`** (`grep -n materialPreset public/index.html` → no match on `origin/main`) | `public/index.html:1332-1359` |
| Phone clamp `vibThreshold ∈ [0.02, 0.8]`; remote `vibThreshold` written back to the slider (`round(v·10)`, 1–40) | `public/index.html:1385`, `:1405-1408` |
| Hold / Manual short-circuits `applyPatch` before any vib-related field is applied | `public/index.html:1391` |
| Systems check row "DeviceMotion granted/denied/available" | `public/index.html:1531-1536` |
| Wire rows `absA`/`a`, `micEnergy`, `vibThreshold`, `vibClass` (`none \| physical \| acoustic \| infra_felt`), `materialPreset` (sample payload `"table"`) | `docs/api-contract.md:52`, `:74-79` |
| Backend `MATERIAL_CHANNEL_BIAS` (`handheld`, `table`, `chair`, `speaker` × vib class multipliers) | `services/autoroute-adk/iot_asp_autoroute/priors.py:113-118` |
| `vib_algo_weights(vib_class, material_preset)` scales `VIB_ALGO_WEIGHTS[vib]` by the bias; `preferred_algos`, `next_algo_weighted` | `priors.py:158-200` |
| Patch author reads `telemetry["materialPreset"]`, feeds it to the weighted rotate and echoes it in the patch | `services/autoroute-adk/iot_asp_autoroute/sudden_freq.py:76-78`, `:128-129` |
| Backend clamp `vibThreshold ∈ [0.01, 2.0]` (`CLAMPS`), `validate_patch` refuses out-of-range | `services/autoroute-adk/iot_asp_autoroute/clamps.py:24`, `:77-89` |
| Authoritative vib anomaly detector (SciPy medfilt + MAD z-score, 1 Hz, 0.0005 g quantum) | `services/autoroute-adk/iot_asp_autoroute/vib_anomaly.py:24-27`, `:50-149` |
| Policy prose: routing table, debounce ≥250–400 ms, chair-node bias | `docs/algorithms.md:33-44`; `README.md:25-35` ("Vibration policy (parked — material-dependent)") |

## Remaining scope

All phone changes go in one delimited block `// ══ vib channels (#4 #5 #6) ══` next to the telemetry
section (rule: `.claude/rules/public-frontend.md`), additive under `schemaVersion: 1`.

1. **Channel arming model (#6):** two booleans `armPhysical`, `armAcoustic` persisted as
   `hop.armPhysical` / `hop.armAcoustic` (default both `true` when *Vib auto* is on — today's behaviour).
   `updateVibClass` ignores `physical`/`infra_felt` when `armPhysical` is false and `acoustic` when
   `armAcoustic` is false. A `materialPreset` `<select>` (`handheld | table | chair | speaker`, persisted
   as `hop.materialPreset`) sets the arming defaults from the table in *Goal* and is emitted in telemetry.
2. **Physical channel (#4):**
   - Gravity handling: when `e.acceleration` is `null` (some WebKit builds expose only
     `accelerationIncludingGravity`), subtract a slow EMA (τ ≈ 2 s) of `accelerationIncludingGravity`
     instead of the current `Math.hypot` on the raw vector, so a still phone reads ≈ 0 g rather than ≈ 1 g.
   - Units: DeviceMotion reports m/s²; convert to **g** (`/ 9.80665`) before comparing against
     `vibThreshold` and before beaconing `absA` — the backend detector (`vib_anomaly.py`) is documented in g.
   - **Shake action:** when `accelMag` exceeds `3·thr` for two consecutive events within 400 ms and
     `armPhysical` is true → `shakeCount++`, force one immediate hop (`pending.length = 0; nextHopAt =
     ctx.currentTime + 0.05; schedule()`), and every 4th shake calls `reseed("shake")` (spec 02).
     Debounced ≥ 300 ms like `routeFromVib`.
3. **Acoustic channel (#5):** promote the existing `> -55 dB` rule to a burst detector: keep a 1 s rolling
   median of `acousticEnergy`; `acousticBurst = acousticEnergy − median ≥ 12 dB` (same 12 dB margin the
   sudden-freq detector uses at `:745`). A burst sets `vibClass = "acoustic"` (if armed) and, when #25's
   `micDiff` is available, uses `micDiff` instead of `micEnergy` so the phone's own carrier does not
   trigger it.
4. **Telemetry:** emit `materialPreset` (string) and reuse existing names for everything else. `absA`
   stays the EMA magnitude; per-axis values go through #26's `ax` `ay` `az` / `accelAxes`, not new keys.
5. **Backend:** nothing new is required — `MATERIAL_CHANNEL_BIAS` and `sudden_freq.author_sudden_freq_patch`
   already consume `materialPreset`. Add a negative-control test that an unknown preset (`"granite"`)
   yields bias `1.0` (already the `dict.get(...).get(vib, 1.0)` behaviour at `priors.py:166`).
6. **Docs:** README's vibration-policy table gains the `materialPreset` column above and links here.

## Wire fields

All names exist in [`docs/api-contract.md`](../api-contract.md); this spec adds none.

| Field | Direction | Notes |
|-------|-----------|-------|
| `vibClass` | telemetry | `none \| physical \| acoustic \| infra_felt` (unchanged) |
| `absA` / `a` | telemetry | accel magnitude in **g** after item 2 (today: m/s² EMA — a documented unit drift to fix) |
| `micEnergy` | telemetry | mean 17–23 kHz dBFS (unchanged) |
| `vibThreshold` | telemetry + patch | slider/10; patch-clamped 0.02–0.8 on phone, 0.01–2.0 on backend |
| `materialPreset` | telemetry | `handheld \| table \| chair \| speaker` — documented, **not yet emitted** |
| `ax` `ay` `az` / `accelAxes`, `gx` `gy` `gz` / `gyroAxes` | telemetry | per-axis, owned by #26 |
| `micDiff`, `bandBurst`, `soundBurst` | telemetry | owned by #25; consumed by item 3 |

## Clamps / safety

- `vibThreshold` clamps are unchanged: phone `[0.02, 0.8]` (`index.html:1385`), backend `[0.01, 2.0]`
  (`clamps.py:24`). A patch outside the backend range is **refused**, never rewritten.
- Vib routing only ever picks from the UI aliases `hop | pulse | shriek` (`routeFromVib`); the backend
  whitelist `ALLOWED_ALGOS` (`clamps.py:7-9`) is untouched.
- **Hold / Manual:** local vib routing is a local decision and continues under Hold (issue text:
  "local suddenFreq rotate may continue"); remote patches carrying `vibThreshold`/`materialPreset`
  are refused at `applyPatch` (`:1391`) and by `tools.write_patch` when the latest telemetry has `holdManual`.
- DeviceMotion permission is requested only from a user gesture (`setVibAuto` → `ensureMotion`); never on load.
- Mic capture keeps `echoCancellation/noiseSuppression/autoGainControl: false` and is never routed to output.
- No PII: accelerometer magnitudes, mic band energy, and a material word are device metrics; no audio is uploaded.

## Acceptance tests

Static (`tests/test_public_html.py`, additive):

1. `addEventListener("devicemotion"` present exactly once; `DeviceMotionEvent.requestPermission` present.
2. `e.acceleration || e.accelerationIncludingGravity` present (gravity-excluded preferred).
3. `materialPreset` appears in `telemetryPayload()` body once the block lands (assert presence); the
   `<select>` options are exactly `handheld`, `table`, `chair`, `speaker`.
4. `9.80665` present (m/s² → g) once item 2 lands.
5. `Hold / Manual`, `holdManual`, `holdPatchBtn` literals intact (existing gate).

Backend (`tests/test_priors_material.py`, new, stdlib + numpy only):

6. `vib_algo_weights("physical", "chair")["burst"] == 0.40 * 1.3` and `vib_algo_weights("physical", "granite") == VIB_ALGO_WEIGHTS["physical"]` (unknown preset → no scaling).
7. `preferred_algos("acoustic", "speaker")[0] == "am_gate"`; `next_algo_weighted("hop", "acoustic", "speaker")` returns the next entry of that tuple.
8. `author_sudden_freq_patch({... "materialPreset": "table", "vibClass": "physical", "suddenFreq": True})` → `ok` and `patch["materialPreset"] == "table"`; with `holdManual: True` → refused.

Browser (`tests/e2e/public_smoke.spec.mjs`): 9. dispatching a synthetic `devicemotion` event with
`acceleration = {x: 0, y: 0, z: 30}` while *Vib auto* is on flips the pill to `physical` within 100 ms and
`telemetryPayload().vibClass === "physical"`.

## CI gate

- `tests` job (`python3 -m pytest tests -q`) runs the static and backend tests above; `static_gates` is
  unchanged (Hold/Manual literals, no keys, `schemaVersion: 1`).
- No new job. The e2e test is optional (spec 01's Playwright lane).

## Risks / HW limits

- iOS Safari exposes DeviceMotion only after `requestPermission()` from a gesture and only in secure
  contexts; some builds deliver `acceleration = null` and only `accelerationIncludingGravity`
  (MDN BCD issue #6217; p5.js #4750 — see Sources). The fallback path is therefore mandatory, not optional.
- DeviceMotion is a ~60 Hz sample stream of the phone body; it cannot resolve true infrasound and is a
  **felt proxy** only (`docs/algorithms.md:27-31`).
- The 17–23 kHz mic band is at the edge of the phone mic's response and of the A2DP codec; `micEnergy`
  is a relative indicator, not a calibrated SPL (`SPEC.md` § Relevance).
- Unit drift: today `absA` is an m/s² EMA while `vib_anomaly.py` documents g. Fixing it changes the scale
  of stored telemetry; the backend detector is threshold-relative (MAD z-score), so old and new series
  must not be concatenated in one window.
- BT latency (tens–hundreds of ms) makes a "forced hop on shake" audible later than the shake.

## Sources

- GitHub issues #4, #5, #6 (read via the GitHub connector, 2026-09-08) — scope tables above are quoted from them.
- Firecrawl developer search → MDN browser-compat-data issue #6217 (Safari requires
  `DeviceMotionEvent.requestPermission`; added iOS 14.5 per BCD) and processing/p5.js issue #4750
  (`acceleration` may be unavailable on iOS; fall back to `accelerationIncludingGravity`).
- Firecrawl developer search → vueuse `useDeviceMotion` docs: `acceleration`, `accelerationIncludingGravity`,
  `rotationRate`, `interval`; permission trigger must be bound to user interaction on iOS.
- Repo: `reference/knowledge/mdn-devicemotion/*.md` (MDN `DeviceMotionEvent` digests), `docs/algorithms.md`,
  `docs/physics.md`, `README.md` § Vibration policy, `docs/api-contract.md`, `priors.py`, `sudden_freq.py`,
  `clamps.py`, `vib_anomaly.py`, `public/index.html` (`origin/main` @ `0625e91`, lines cited above).
- Literature (from `reference/LITERATURE.md`, mirrored in `priors.CITATIONS`): PMID 27780424 (human–seat
  coupling), arXiv:2211.03647 (seismo-acoustic coupling analogy).
