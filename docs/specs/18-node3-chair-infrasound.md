# #18 — Node 3 chair-taped phone + infrasound LF-accel proxy (`infra_felt`)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/18 · Labels: `enhancement`, `parked` · Related: #4/#5 ([04-06-vibration-channels.md](04-06-vibration-channels.md)), #9 (native SensorKit), #25 ([25-hw-limited-lf-aec-micdiff.md](25-hw-limited-lf-aec-micdiff.md)), #26 ([26-colab-live-gcs-features.md](26-colab-live-gcs-features.md))

## Status

**Parked — priors shipped, node not deployed.** The backend already treats `infra_felt` as a first-class
vib class (prior text, citations, algo weights, LF band gating) and the phone already emits
`vibClass: "infra_felt"` from a crude LF accelerometer proxy. What is parked is the **third node itself**
(an iPhone taped to a chair), a chair-specific `materialPreset: "chair"` arming default, a better LF
proxy (band-limited 0.5–20 Hz energy instead of a gravity-magnitude delta low-pass), and the honesty copy
in the UI. This spec is the design record; no implementation lands with it.

## Goal

1. **Fleet split:** nodes 1–2 (iPhone 16 ↔ Soundcore 2, different rooms) stay acoustic-first; **node 3**
   (a future iPhone, e.g. 14) is **mechanically coupled to a chair** and is physical / structure-borne
   first. Chair/frame/floor coupling dominates free handheld motion.
2. **Infrasound (felt-not-heard, <20 Hz) as a third sensing class** next to near-ultrasonic TX and the
   audible mic: Safari + Bluetooth **cannot** capture or play true infrasound (high-pass everywhere), so the
   practical proxy is **LF linear-accelerometer energy** from `DeviceMotion`, reported as `lfEnergy` and
   classified as `infra_felt`.
3. Route `infra_felt` toward `infra_mod` / higher pulse-shriek duty, and open the optional LF TX band
   10–20 Hz **only** when `lfDriveCapable` is true (never for the web fleet).
4. Dedicated infrasound mic / geophone stays **future research only** (native hardware, #9 / #14).

## Shipped on `main`

Verified by reading `origin/main` @ `0625e91` (backend files identical on this branch):

| What | Where |
|------|-------|
| Phone LF proxy: `lfMag = 0.92·lfMag + 0.08·|gmag − lfMag|` from `accelerationIncludingGravity`; `infra_felt` when `lfMag > 0.35·thr` | `public/index.html:764-771` |
| `infra_felt` routes to `shriek`/`pulse` locally (300 ms debounce) | `public/index.html:655-667` |
| `vibClass` on the wire with `infra_felt` as an allowed value | `docs/api-contract.md:79` |
| `lfEnergy` / `usEnergy` (dB) and `bandBurst` (`lf \| us \| both`) documented; `lfArmed` / `lfDriveCapable` default `false` for the web fleet | `docs/api-contract.md:83`, `:90-92` |
| Backend `lfGate = lfArmed ∧ lfDriveCapable ∧ vibClass == infra_felt` | `docs/api-contract.md:94-95`; `services/autoroute-adk/iot_asp_autoroute/fleet_log.py:222` |
| `PRIORS["infra_felt"]` (Safari/BT cannot claim <20 Hz; LF accel proxy → `infra_mod`; TX 10–20 Hz only when `lfDriveCapable`; cites PMID 33940893 / DOI 10.1121/10.0003509, DOI 10.1121/1.5063819) | `services/autoroute-adk/iot_asp_autoroute/priors.py:25-30` |
| `VIB_ALGO_WEIGHTS["infra_felt"]` = `infra_mod 0.45, am_gate 0.30, burst 0.25, …` | `priors.py:86-93` |
| `MATERIAL_CHANNEL_BIAS["chair"]` = `acoustic 0.7, physical 1.3, infra_felt 1.4` | `priors.py:116` |
| `lf_drive_capable()` (Hold → False; `lfDriveCapable is True`; or `lfArmed` + LF band tag) | `priors.py:203-216` |
| `prior_keys_for_event` adds `infra_felt` when `vibClass == infra_felt` or LF-capable | `priors.py:219-234` |
| `band_for_telemetry` → `("10-20", …)` only when capable **and** (`infra_felt` or LF tag), else `17-23k` | `priors.py:237-267` |
| `duty_bias_for_vib("infra_felt")` = `pulseMs +20`, `shriekMs +15` | `priors.py:270-277` |
| `seismo_bundle()["honesty"]`: "LF accel is a felt proxy; true infrasound mic/TX requires lfDriveCapable." | `priors.py:290-293` |
| Clamps: `BAND_LF = (10, 20)`; `band_limits` picks LF only from an explicit tag or `fMin ≤ 100` | `services/autoroute-adk/iot_asp_autoroute/clamps.py:13`, `:30-43` |
| Agent instruction: LF band ONLY when `lfDriveCapable` and `vibClass=infra_felt` | `services/autoroute-adk/iot_asp_autoroute/agent.py:40-41` |
| Feature projector: `band_burst(lf_energy, us_energy)` with `BAND_LF_THR_DB = -60` — "Heuristic labels only (not infrasound capture)" | `services/autoroute-adk/iot_asp_autoroute/features_live.py:80`, `:158-179` |
| Fleet topology "Optional 3rd node: phone chair-mounted for structure-borne / accelerometer-biased sensing" | `SPEC.md:28-33`; `docs/algorithms.md:8-16` (node 3 **Parked**), `:25`, `:27-31`, `:44` |
| Physics honesty: "Safari + BT speaker/mic: no faithful infrasound TX/RX; LF accel is a proxy" | `docs/physics.md:11`, `:31-35`; `CLAUDE.md` invariant 8 |

## Remaining scope

1. **Node 3 profile (phone):** `materialPreset: "chair"` (spec 04-06 `<select>`) sets `armPhysical = true`,
   `armAcoustic = false` by default and a lower `vibThreshold` default (`0.08`, slider 8). The systems
   check row reads "Node role: chair (structure-borne first)". Nothing else differs — same URL, same
   incoherent seed, same A2DP TX (node 3 may transmit or be sensor-only; both are allowed).
2. **Better LF proxy (phone):** replace the gravity-magnitude delta low-pass with a band-limited
   estimate: keep a 4 s ring of `|acceleration|` samples at the DeviceMotion rate (`e.interval`),
   compute `lfEnergy = 10·log10(mean square of the 0.5–20 Hz component)` via a two-pole IIR band-pass
   (no FFT on the phone), `usEnergy` stays the mic 17–23 kHz mean (#25). `infra_felt` when
   `lfEnergy ≥ -60 dB` (mirrors `BAND_LF_THR_DB`) **and** `accelMag` is below the `physical` threshold
   (sway without thumps). Emit `lfEnergy` in telemetry (name already documented).
3. **Honesty copy (phone):** the vib pill tooltip and the systems check state "LF accel = felt proxy, not
   infrasound capture"; the LF TX toggle stays hidden unless `lfDriveCapable` is set by a native shell.
4. **Backend:** none for the priors. `features_live.build_feature_record` already labels `bandBurst`;
   add a `chair` fixture to `demo_points` so the dry-run shows an `infra_felt` → `infra_mod` decision.
5. **Docs:** `docs/algorithms.md` node-3 row flips from **Parked** to **Pilot** when a phone is taped.

## Wire fields

All already in [`docs/api-contract.md`](../api-contract.md):

| Field | Direction | Use here |
|-------|-----------|----------|
| `vibClass` | telemetry | `infra_felt` from item 2 |
| `lfEnergy`, `usEnergy` | telemetry | dB band energies (LF is the accel proxy, US is mic) |
| `bandBurst` | telemetry / features | `lf \| us \| both` |
| `lfArmed`, `lfDriveCapable` | telemetry | stay `false` on the web fleet; backend derives `lfGate` |
| `materialPreset` | telemetry | `chair` for node 3 |
| `band` | telemetry + patch | `10-20` only when `lfGate`; otherwise `17-23k` |
| `absA` / `a`, `ax` `ay` `az` / `accelAxes` | telemetry | magnitude + per-axis (#26) |

## Clamps / safety

- LF TX band `[10, 20]` Hz is only reachable through `band_for_telemetry` when `lf_drive_capable()` is
  true; `holdManual` forces it false (`priors.py:207-208`). `validate_patch` refuses `fMin`/`fMax` outside
  the selected band (`clamps.py:67-75`). No web phone ever gets a `10-20` patch.
- `infra_felt` duty bias (`+20` / `+15` ms) is applied **inside** `pulseMs` 20–200 / `shriekMs` 20–120
  (`sudden_freq.py:82-84`).
- `vol` unaffected; residential gain remains a human setting.
- No medical or CFD claims: infrasound citations are exposure/perception context only (`priors.CITATIONS`
  roles), and the prior text says so.
- No PII: a chair is a material word; no room names, addresses or occupant identifiers in telemetry
  (the fleet copy is generic: "different rooms").

## Acceptance tests

Backend (`tests/test_priors_infra.py`, new):

1. `band_for_telemetry({"vibClass": "infra_felt"})[0] == "17-23k"` (not capable → US band).
2. `band_for_telemetry({"vibClass": "infra_felt", "lfDriveCapable": True})[0] == "10-20"` with `fMin/fMax` inside `[10, 20]`.
3. `band_for_telemetry({"vibClass": "infra_felt", "lfDriveCapable": True, "holdManual": True})[0] == "17-23k"`.
4. `preferred_algos("infra_felt", "chair")[0] == "infra_mod"`; `vib_algo_weights("infra_felt", "chair")["infra_mod"] == 0.45 * 1.4`.
5. `author_sudden_freq_patch({... "vibClass": "infra_felt", "materialPreset": "chair", "shriekMs": 110})` → `shriekMs == 120` (clamped, not refused) and `"infra_felt" in patch["priors"]`.
6. `features_live.band_burst(-55, -90) == "lf"`, `band_burst(-90, -30) == "us"`, `band_burst(-55, -30) == "both"`, `band_burst(None, None) == "none"` (whatever the existing "no burst" label is — assert against the constant, not a literal).

Static (`tests/test_public_html.py`, once item 2 lands): 7. `lfEnergy` appears in `telemetryPayload()`;
8. the literal `felt proxy` appears in the systems-check copy; 9. no `fMin`/`fMax` default below 17000.

## CI gate

- `tests` job blocks on 1–6 (stdlib + numpy; no network). `autoroute` job's `scripts/autoroute_dev.sh`
  dry-run continues to exercise the `infra_felt` fixture once item 4 lands.
- `static_gates` unchanged (clamp constants `BAND_LF = (10, 20)` asserted by CI already).

## Risks / HW limits

- **True infrasound is out of reach for this fleet:** consumer BT speakers and phone mics are high-passed;
  Safari cannot play or capture <20 Hz. `lfEnergy` is body/chair sway measured by the accelerometer — a
  *felt* proxy (`docs/algorithms.md:27-31`, `docs/physics.md:31-35`).
- DeviceMotion sample rate on iOS is ~60 Hz with coarsened timing; a 0.5–20 Hz band-pass is feasible but
  aliasing from thumps (>30 Hz) must be attenuated by the `physical` threshold guard.
- Taping a phone to a chair couples it to whoever sits there: literature on human–seat coupling
  (PMID 27780424, 2026 seated-WBV studies in `reference/LITERATURE.md`) says transmissibility depends on
  posture and sex — expect large inter-session variance; thresholds are per node, not fleet-wide.
- A chair-coupled node that also transmits will see its own carrier in the mic; keep node 3 sensor-only or
  rely on #25's `micDiff`.
- Any LF TX (10–20 Hz) needs native hardware (`lfDriveCapable`); the Soundcore 2 has no useful output there
  (`SPEC.md` — frequency response not even listed by the vendor).

## Sources

- GitHub issue #18 (read via the GitHub connector, 2026-09-08) — fleet split, infrasound honesty bullets.
- Literature IDs (all in `reference/LITERATURE.md` and mirrored in `priors.CITATIONS`): PMID 33940893 /
  DOI 10.1121/10.0003509 (wind-turbine infrasound annoyance/perception), DOI 10.1121/1.5063819 (VHFS/US
  exposure ethics, Part I), PMID 27780424 (human–seat coupling), arXiv:2211.03647 (seismo-acoustic coupling
  analogy); PubMed PMC7034801 (auditory-cortex activation by LFS/infrasound) — perception context only.
- Repo: `docs/algorithms.md`, `docs/physics.md`, `SPEC.md`, `docs/api-contract.md`, `priors.py`, `clamps.py`,
  `sudden_freq.py`, `fleet_log.py`, `features_live.py`, `agent.py`, `public/index.html`
  (`origin/main` @ `0625e91`, lines cited above), `reference/knowledge/apple-coremotion/*.md` (Core Motion
  digests — native path only).


## Balanced PR4 — chair mount checklist (parked)

- [ ] Physical: phone taped/strapped to chair frame (not handheld)
- [ ] Telemetry: `vibClass=infra_felt` dominates; document handheld vs chair delta
- [ ] Honesty UI: "felt proxy via accel — not infrasound mic"
- [ ] TX: do not arm 10–20 Hz unless `lfDriveCapable` (Soundcore = false)
- [ ] Sonos Beam (#39) is an **alternate** Node 3 sink research path — do not conflate with chair mech coupling

No HW claimed present in this Balanced stack pass.
