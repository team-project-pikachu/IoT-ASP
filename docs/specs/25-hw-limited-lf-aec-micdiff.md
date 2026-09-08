# #25 — HW-limited: LF mic/TX + full AEC for `soundBurst` `micDiff`

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/25 · Branch: `claude/mdc-conversion-features-gu3yzk` · Related: #9 (native companion), #18 (phone-speaker LF experiment), #26 (Colab features consume `micDiff`)

## Status

**HW-limited — do not block public hop redeploys on this issue** (issue body, "Do not"). The four
leftovers below are limits of iOS web audio, consumer Bluetooth speakers, and phone microphones, not
bugs in this repository. What this item ships is the **honest backend side**: a small numpy-allowed
helper module `services/autoroute-adk/iot_asp_autoroute/mic_diff.py` that (a) computes the same
best-effort `micDiff = micEnergy − α·outLevel` the phone uses, (b) calibrates α per device / BT route
from TX-only pairs, (c) answers "can this fleet do full AEC / LF mic / LF TX?" with a fixed, cited
**no / no / only-if-`lfDriveCapable`**, (d) turns `micDiff` into a clamped burst → `shriek_chirp` bias
that always yields to Hold / Manual, and (e) exposes the leftover list as a report for the ADK agent.

**Implemented on branch `claude/mdc-conversion-features-gu3yzk` (2026-09-08):**
`services/autoroute-adk/iot_asp_autoroute/mic_diff.py`, `tests/test_mic_diff.py` (19 tests, MD-01 … MD-17)
and `.vv/burst-shriek.md` now exist; see *Shipped on `main`* → "This item" and the *Implementation
deltas* note under *Acceptance tests*. The integrator hooks (§ Remaining scope 4) are still requests.

On the base checkout (`4e4f5db`) the public HTML does **not** yet emit `micDiff` / `outLevel` / `soundBurst` / `extremeActive` /
`lfEnergy` / `usEnergy` (`grep` over `public/` returns nothing — see *Shipped on main*). The owner's
Mac clone is described by the issue as ahead ("shipped in public hop UI"); this spec therefore treats
every burst key as an **optional telemetry input** and computes `micDiff` server-side when absent.

## Goal

1. One authoritative definition of `MIC_DIFF_ALPHA = 0.85` and `mic_diff()` in the backend package
   so `sudden_freq.py`, `tools.py` and the #26 feature projector never re-implement the subtraction.
2. A deterministic, refusing calibrator (`calibrate_alpha`) so α can be tuned per device / BT route
   from TX-only measurements (issue "Optional: calibrate α per device / BT route").
3. Capability answers (`aec_capability`, `lf_capability`) that are **always honest** for the web fleet:
   no full AEC, no LF mic, LF TX only via `priors.lf_drive_capable`.
4. A burst decision (`burst_decision`) + pure patch bias (`apply_burst_bias`) so an environmental burst
   biases the autoroute toward `shriek_chirp` with `shriekMs + 15` **inside clamps**, and is refused
   outright under `holdManual`.
5. `hw_limits_report()` — the four HW-limited leftovers with pointers to `docs/algorithms.md`,
   `docs/iphone-bluetooth.md` and the native-companion path (#9) — callable as an ADK tool.

## Shipped on `main`

Verified by reading the files on this checkout (line numbers exact at `4e4f5db`):

| What | Where |
|------|-------|
| Telemetry contract already declares `outLevel`, `micDiff = micEnergy − 0.85·outLevel` ("best-effort AEC; browser cannot do full AEC"), `bandBurst`, `soundBurst` / `extremeActive`, `lfEnergy` / `usEnergy` | `docs/api-contract.md:88-92` |
| `lfArmed` / `lfDriveCapable` rows ("web fleet defaults `false` — #22/#25") | `docs/api-contract.md:83` |
| Phone mic capture requests `echoCancellation:false, noiseSuppression:false, autoGainControl:false, channelCount:1, sampleRate:48000` with the comment "every one of them will annihilate a 20 kHz carrier" | `public/index.html:937-944`; diagnostics copy at `:1516`, `:1521` ("AEC/NS/AGC off") |
| Mic analyser `fftSize = 2048`, `minDecibels = -130`, never routed onward ("that is feedback") | `public/index.html:953-956` |
| TX analyser `fftSize = 16384`, bin width `ctx.sampleRate / an.fftSize` | `public/index.html:794`, `:729` |
| Beacon carries `micEnergy: acousticEnergy` only — **no** `micDiff` / `outLevel` / burst keys on this checkout | `public/index.html:1348` (`grep -n "micDiff\|outLevel\|soundBurst\|extremeActive\|lfEnergy\|usEnergy" public/index.html` → no matches) |
| Web Audio ↔ A2DP constraint C1 and "disable AEC/NS/AGC on mic capture where supported" | `docs/DESIGN_CONSTRAINTS.md` C1 table; `docs/iphone-bluetooth.md:18` |
| Native / Xcode shell (#9) is the only path to `AVAudioSession` and HFP mic-on-accessory | `docs/iphone-bluetooth.md:30-37` |
| "Consumer BT speakers/mics **high-pass**; Safari cannot cleanly play or capture true infrasound"; LF accel energy is the felt proxy | `docs/algorithms.md:27-31`, `:25` |
| LF TX gate `lf_drive_capable(telemetry)` (`holdManual` → `False`; `lfDriveCapable is True`; or `lfArmed` + LF band tag) | `services/autoroute-adk/iot_asp_autoroute/priors.py:203-216` |
| LF band selection `band_for_telemetry` — `10-20` only when capable AND (`infra_felt` or LF tag) | `priors.py:237-267`; `LF_BAND_HZ`/`US_BAND_HZ` at `priors.py:122-123` |
| `infra_felt` prior text (Safari/BT cannot claim <20 Hz; TX 10–20 Hz only when `lfDriveCapable`) | `priors.py:25-30`; `seismo_bundle()["honesty"]` at `priors.py:290-293` |
| Shriek duty bias per vib class (`infra_felt` → `shriekMs + 15`, others `+5`) | `priors.py:270-277` (`duty_bias_for_vib`) |
| Patch author: `holdManual` refuse first; `shriek = clamp(20, 120, shriek + bias)`; `validate_patch` last | `services/autoroute-adk/iot_asp_autoroute/sudden_freq.py:67-68`, `:82-84`, `:130-131` |
| `is_sudden_freq_event` returns `False` under `holdManual` | `sudden_freq.py:42-45` |
| Clamp constants `shriekMs (20, 120)`, `ALLOWED_ALGOS` incl. `shriek_chirp` | `services/autoroute-adk/iot_asp_autoroute/clamps.py:7-9`, `:19-25` |
| `write_patch` refuses on `holdManual` in the patch **or** latest telemetry | `services/autoroute-adk/iot_asp_autoroute/tools.py:61-66`; `process_sudden_freq` refuse at `tools.py:167-168` |
| ADK tool registration pattern (plain functions in `tools=[…]`) | `services/autoroute-adk/iot_asp_autoroute/agent.py:17-25`, `:52-60`; agent instruction already says "Respect Hold/Manual" (`agent.py:44`) |
| numpy is already a runtime dependency (`vib_anomaly.py`) | `services/autoroute-adk/requirements.txt` (`numpy>=1.26.0,<3`); `vib_anomaly.py:14` |
| #26 spec expects a `micDiff` helper with α = 0.85 and `shriekBias = soundBurst ∨ extremeActive ∨ micDiff > 6` | `docs/specs/26-colab-live-gcs-features.md:76`, `:81`, `:144`, `:148` |

**This item (branch, 2026-09-08):**

| What | Where |
|------|-------|
| Constants `MIC_DIFF_ALPHA = 0.85`, `MIC_DIFF_THR_DB = 6.0`, `ALPHA_RANGE = (0.0, 2.0)`, `MIN_CAL_PAIRS = 3`, `SHRIEK_MS_BIAS = 15`, `BURST_ALGO = "shriek_chirp"` (asserted `in ALLOWED_ALGOS` at `:53`), `MIC_FFT_SIZE`/`TX_FFT_SIZE`/`WEB_SAMPLE_HZ` | `services/autoroute-adk/iot_asp_autoroute/mic_diff.py:37-48` |
| `mic_diff`, `mic_diff_from_telemetry` (phone `micDiff` wins; missing `outLevel` → passthrough) | `mic_diff.py:79`, `:98` |
| `calibrate_alpha` — `numpy.linalg.lstsq(out[:, None], mic, rcond=None)`, rank-0 refuse, `[0, 2]` clamp, `< 3` pairs refuse; numpy imported lazily inside the function | `mic_diff.py:126` |
| `aec_capability` (`fullAEC` hard-coded `False`; UA classified by `_ua_class` `:176`, never echoed) | `mic_diff.py:188` |
| `lf_capability` (`lfMic` hard-coded `False`; `lfTx = priors.lf_drive_capable`) | `mic_diff.py:214` |
| `burst_decision`, `burst_decision_from_telemetry`, `apply_burst_bias` (Hold / Manual refuse first; `shriekMs` clamped to `CLAMPS["shriekMs"]`) | `mic_diff.py:263`, `:290`, `:309` |
| `hw_limits_report` — four limits `full_aec`, `lf_mic`, `lf_tx`, `alpha_calibration` (`_LIMITS` data at `:334`) | `mic_diff.py:377` |
| `demo()` (seed 25) + `main()` CLI (`--demo` → exit 0; no args → usage on stderr, exit 2) | `mic_diff.py:400`, `:422` |
| Tests MD-01 … MD-17 | `tests/test_mic_diff.py` |
| Evidence | `.vv/burst-shriek.md` |

## Remaining scope

### 1. `services/autoroute-adk/iot_asp_autoroute/mic_diff.py`

Imports: stdlib (`json`, `math`, `sys`, `argparse`, `typing`) + `numpy` (allowed by the brief; used only in
`calibrate_alpha`). Package-internal: `from .clamps import CLAMPS, validate_patch`, `from .priors import
lf_drive_capable, normalize_vib_class`. **No** scipy, no `google.*`, no `gcs_io`, no I/O other than
stdout in `--demo`.

Constants (module level, asserted by tests):

| Name | Value | Meaning |
|------|-------|---------|
| `MIC_DIFF_ALPHA` | `0.85` | Output-bus subtraction weight (matches `docs/api-contract.md:89`) |
| `MIC_DIFF_THR_DB` | `6.0` | Burst threshold on `micDiff` (matches #26 `shriekBias`) |
| `ALPHA_RANGE` | `(0.0, 2.0)` | Calibration clamp |
| `MIN_CAL_PAIRS` | `3` | Below this `calibrate_alpha` refuses |
| `SHRIEK_MS_BIAS` | `15` | Added to `shriekMs` on a burst, then clamped to `CLAMPS["shriekMs"]` |
| `BURST_ALGO` | `"shriek_chirp"` | Wire name (in `ALLOWED_ALGOS`) |
| `MIC_FFT_SIZE`, `TX_FFT_SIZE`, `WEB_SAMPLE_HZ` | `2048`, `16384`, `48000` | Mirrors `public/index.html:953`, `:794`, `:787` for the LF-resolution argument |

Functions (all pure; never mutate inputs):

| Function | Contract |
|----------|----------|
| `mic_diff(mic_energy_db, out_level_db, alpha=MIC_DIFF_ALPHA) -> float` | `round(mic − alpha·out, 3)`. `None` / non-numeric / non-finite `mic_energy_db` or `out_level_db` coerce to `0.0` (so a missing `outLevel` makes `micDiff == micEnergy` — passthrough). `alpha` `None`/non-finite → `MIC_DIFF_ALPHA`. Never raises. |
| `mic_diff_from_telemetry(t, alpha=None) -> float \| None` | If `t.get("micDiff")` is a finite number → return it unchanged (phone wins, same rule as #26). Else if `micEnergy` is a finite number → `mic_diff(micEnergy, outLevel, alpha or MIC_DIFF_ALPHA)`. Else `None`. |
| `calibrate_alpha(pairs) -> dict` | `pairs`: iterable of `(micEnergy, outLevel)` measured **with TX only** (quiet room; `soundBurst` false). Drops pairs that are not two finite numbers. If fewer than `MIN_CAL_PAIRS` remain → `{"ok": False, "alpha": MIC_DIFF_ALPHA, "n": n, "residual_rms": None, "clamped": False, "reason": "need >= 3 TX-only pairs, got n"}`. If all `outLevel` are zero (rank 0, no variance) → same shape, reason `"outLevel has no variance"`. Else `alpha_raw = numpy.linalg.lstsq(out[:, None], mic, rcond=None)[0][0]` (least squares **through the origin**, `M×1` design matrix so `rank == 1`), `alpha = min(2.0, max(0.0, alpha_raw))`, `clamped = alpha != alpha_raw`, `residual_rms = sqrt(mean((mic − alpha·out)²))` computed with the **clamped** alpha, `"reason": "ok"` (or `"alpha clamped from <raw>"` when clamped). All floats rounded to 4 dp; `n` is the number of used pairs. |
| `aec_capability(user_agent=None) -> dict` | Always `{"fullAEC": False, "path": "output-bus-subtraction", "alpha": MIC_DIFF_ALPHA, "userAgentClass": …, "reason": …, "nativePath": "#9 AVAudioSession / HFP (docs/iphone-bluetooth.md)", "docs": ["docs/iphone-bluetooth.md", "docs/api-contract.md"]}`. `userAgentClass`: `"unknown"` for `None`/empty; `"ios-chrome"` when the UA contains `CriOS` and (`iPhone` or `iPad`); `"ios-safari"` when it contains `iPhone`/`iPad` and `Safari` but not `CriOS`; else `"other"`. `fullAEC` is `False` for every class — browser AEC is a speech-mode processor the page must disable (`public/index.html:937-944`) and the UA string cannot make a web page do carrier-band echo cancellation. `reason` names both facts and that the constraint is advisory (browsers ignore unknown/unhonoured constraints — MDN). |
| `lf_capability(telemetry) -> dict` | `{"lfTx": priors.lf_drive_capable(telemetry), "lfMic": False, "micBinHz": round(WEB_SAMPLE_HZ / MIC_FFT_SIZE, 2)` (= `23.44`), `"txBinHz": round(WEB_SAMPLE_HZ / TX_FFT_SIZE, 2)` (= `2.93`), `"lfBandHz": [10.0, 20.0]`, `"reasons": [...]}`. `reasons` always contains `"lfMic: consumer mic/BT high-pass (docs/algorithms.md § Infrasound honesty)"` and `"lfMic: micAnalyser fftSize 2048 @ 48 kHz -> 23.44 Hz/bin; <20 Hz is bin 0"`; adds `"lfTx: gated by lfDriveCapable (priors.lf_drive_capable)"` when `lfTx` is `False`, `"lfTx: lfDriveCapable asserted by telemetry"` when `True`, and `"holdManual"` when `telemetry.get("holdManual")`. `telemetry=None` → `lfTx False`. `lfMic` is **never** `True` (web fleet). |
| `burst_decision(mic_diff_db, thr_db=MIC_DIFF_THR_DB, hold_manual=False, vib_class=None) -> dict` | Keys in this order: `extreme`, `algo`, `shriekMsBias`, `thrDb`, `micDiffDb`, `vibClass`, `reason`. If `hold_manual` (truthy) → `extreme False, algo None, shriekMsBias 0, reason "holdManual — refuse"` **regardless of `mic_diff_db`**. If `mic_diff_db` is `None`/non-numeric/non-finite → `extreme False, algo None, bias 0, reason "micDiff unavailable"`. Else `extreme = mic_diff_db > thr_db` (strict). `extreme` → `algo "shriek_chirp", shriekMsBias 15, reason "micDiff X dB > thr Y dB; vibClass=…"`; not extreme → `algo None, bias 0, reason "micDiff X dB <= thr Y dB"`. `vibClass = priors.normalize_vib_class(vib_class)` (rationale only; it does not change the decision). |
| `burst_decision_from_telemetry(t, thr_db=MIC_DIFF_THR_DB) -> dict` | `hold = bool(t.get("holdManual"))`. If not hold and (`t.get("soundBurst") is True` or `t.get("extremeActive") is True`) → the same dict as an extreme decision with `reason` prefixed `"soundBurst/extremeActive flag"` and `micDiffDb = mic_diff_from_telemetry(t)` (may be `None`). Otherwise `burst_decision(mic_diff_from_telemetry(t), thr_db, hold, t.get("vibClass"))`. |
| `apply_burst_bias(patch, decision) -> dict` | Returns a **copy**. If `not decision.get("extreme")` → unchanged copy. Else set `algo = "shriek_chirp"`, `shriekMs = min(120, max(20, float(patch.get("shriekMs") or 50) + decision["shriekMsBias"]))`, append `"; burst→shriek_chirp (+15 ms)"` to `rationale` (created if absent), set `burstBias = {"micDiffDb": …, "shriekMsBias": 15}` (additive patch field). Never touches `vol`, `fMin`, `fMax`, `band`. The caller still runs `clamps.validate_patch` (this helper never bypasses it; `apply_burst_bias` output on a valid patch is valid by construction — test asserts). |
| `hw_limits_report() -> dict` | `{"issue": 25, "status": "hw-limited", "blocksRedeploy": False, "nativeCompanionIssue": 9, "relatedIssues": [9, 18, 26], "docs": ["docs/algorithms.md", "docs/iphone-bluetooth.md", "docs/api-contract.md", "docs/specs/25-hw-limited-lf-aec-micdiff.md"], "limits": [...]}` with **exactly four** `limits` entries, `id` ∈ `{"full_aec", "lf_mic", "lf_tx", "alpha_calibration"}` in that order, each `{"id", "title", "limitedBy", "shippedPath", "doc", "nativePath"}`: `full_aec` (browser speech-mode AEC only; shipped = output-bus subtraction α = 0.85; doc `docs/iphone-bluetooth.md`; native `#9 AVAudioSession`), `lf_mic` (mic HPF + 23.44 Hz/bin; shipped = `lfEnergy` accel felt proxy; doc `docs/algorithms.md § Infrasound honesty`; native = dedicated infrasound mic/geophone, parked), `lf_tx` (A2DP/Soundcore roll-off; shipped = `10-20` band gated by `lfDriveCapable`; doc `docs/algorithms.md`; native/experimental = Node-3 / phone speaker, #18), `alpha_calibration` (α depends on device + BT route; shipped = `calibrate_alpha` from TX-only pairs; doc = this spec; native = per-route AEC in #9). Pure constant data; JSON-serialisable; contains no URLs other than `docs/` paths and issue numbers. |
| `demo() -> dict` | Deterministic: `random.Random(25)`; 12 TX-only pairs with `outLevel ∈ [-40, -10]` dB and `mic = 0.85·out + N(0, 0.5)` → `calibrate_alpha` (expect `abs(alpha − 0.85) < 0.1`); `micDiff = mic_diff(-20.0, -30.0)` (= `5.5`); `burst` for `{-20, -30}` → not extreme, and for `micEnergy -12` → extreme; `aec_capability("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) … Safari/604.1")`; `lf_capability({"lfDriveCapable": False})`; `burst_decision(20.0, hold_manual=True)` (refused); `hw_limits_report()`. Keys: `micDiff`, `calibration`, `burst`, `burstHold`, `aec`, `lf`, `report`. |
| CLI | `python3 -m iot_asp_autoroute.mic_diff --demo` prints `json.dumps(demo(), indent=2, sort_keys=True)` and exits 0; no args → usage on stderr, exit 2. No network, no GCS, no scipy, no `google-adk`. |

### 2. `tests/test_mic_diff.py` — see *Acceptance tests*.

### 3. `.vv/burst-shriek.md` — evidence: config item, UTC date, commands (`python3 -m pytest
tests/test_mic_diff.py -q`, `cd services/autoroute-adk && python3 -m iot_asp_autoroute.mic_diff --demo`),
exit codes, the demo JSON's `calibration.alpha`, `burst.extreme`, `burstHold.reason`, and a pass/fail
table for the four HW limits (`full_aec` = limited, `lf_mic` = limited, `lf_tx` = gated, `alpha` =
calibrated in demo). No secrets, no site PII.

### 4. Integration (integrator-owned files — requested, **not** edited by this item)

- `sudden_freq.py::author_sudden_freq_patch`, after the shriek/pulse bias (`:82-84`) and before
  `validate_patch` (`:130`):
  ```python
  from .mic_diff import burst_decision_from_telemetry, apply_burst_bias
  burst = burst_decision_from_telemetry(telemetry)
  if burst["extreme"]:
      patch = apply_burst_bias(patch, burst)
  ```
  The existing `holdManual` refuse at `:67-68` runs first, so the bias can never fire under hold.
- `tools.py`: new tool `hw_limits_report() -> dict` returning `mic_diff.hw_limits_report()` (docstring:
  "HW-limited leftovers for #25 — full AEC, LF mic, LF TX, alpha calibration; never blocks redeploys"),
  and `agent.py` `tools=[…]` gains `hw_limits_report`.
- `docs/api-contract.md`: patch table gains the optional additive row `burstBias` (object,
  `{micDiffDb, shriekMsBias}`; present only when a burst biased the patch).
- #26 `features_live.py` may import `mic_diff.MIC_DIFF_ALPHA` and `mic_diff.mic_diff` instead of
  re-implementing (its `given=` passthrough is `mic_diff_from_telemetry`).

## Wire fields

No new **telemetry** fields — all inputs (`micEnergy`, `outLevel`, `micDiff`, `soundBurst`,
`extremeActive`, `lfEnergy`, `usEnergy`, `lfDriveCapable`, `lfArmed`, `holdManual`, `vibClass`) already
exist in `docs/api-contract.md:64-92`. `schemaVersion` stays `1`.

One additive, optional **patch** field (only emitted after the integrator hook lands):

| Field | ★ | Type | Notes |
|-------|---|------|--------|
| `burstBias` | | object | `{"micDiffDb": number \| null, "shriekMsBias": 15}` — present only when a burst biased `algo` → `shriek_chirp`; phones ignore unknown keys |

Semantics restated (canonical text stays in `api-contract.md`): `micDiff = micEnergy − 0.85·outLevel`
(dB); `micDiff > 6 dB` or `soundBurst`/`extremeActive` = environmental burst.

## Clamps / safety

- **Hold / Manual wins:** `burst_decision(..., hold_manual=True)` returns `extreme False` for any
  `micDiff`; `burst_decision_from_telemetry` reads `holdManual` first; `lf_capability` reports `lfTx
  False` under hold because `priors.lf_drive_capable` does (`priors.py:207-208`). The integrator hook
  sits after `sudden_freq.py:67-68`, and `tools.write_patch` re-checks (`tools.py:61-66`).
- **Band clamps untouched:** `apply_burst_bias` never writes `fMin`/`fMax`/`band`/`vol`;
  `shriekMs` is clamped to `CLAMPS["shriekMs"] == (20, 120)` before `validate_patch`, so `shriekMs 110 + 15
  → 120`, never `125`. `vol_hard_max == vol_soft_max == 100.0` untouched.
- **Algo whitelist:** `BURST_ALGO == "shriek_chirp"` is asserted `in ALLOWED_ALGOS` at import.
- **α clamp `[0, 2]` and refusal `< 3` pairs:** a bad calibration set can only produce the default
  `0.85` with `ok False` + reason, never a wild α; the caller must not persist α when `ok` is false.
- **No silent rewrite:** nothing here mutates telemetry; the decision dict carries `reason` for the
  monitor log / rationale.
- **Physics honesty:** `lfMic` is hard-coded `False`, `fullAEC` is hard-coded `False`; `lfEnergy` is
  documented as an accelerometer felt proxy; no infrasound-capture or CFD claims anywhere in the module
  strings (test greps the source for `CFD` and `Navier` — must be absent, and for `proxy` — present).
- **No PII / secrets:** the module has no env reads, no URLs beyond `docs/` paths and issue numbers,
  no device UA strings persisted (UA is classified and discarded).
- **iOS native A2DP only (C1):** the module makes no Bluetooth or device-picker claims; `aec_capability`
  points at `AVAudioSession` (#9) as the only fuller-AEC path.

## Acceptance tests

`tests/test_mic_diff.py` — offline, deterministic (`random.Random(25)`, fixed values), no `tmp_path`
needed except for the CLI test. Run: `python3 -m pytest tests/test_mic_diff.py -q`. Path setup:
`sys.path.insert(0, "services/autoroute-adk")` as the other tests do.

| ID | Check |
|----|-------|
| MD-01 | constants: `MIC_DIFF_ALPHA == 0.85`, `MIC_DIFF_THR_DB == 6.0`, `ALPHA_RANGE == (0.0, 2.0)`, `MIN_CAL_PAIRS == 3`, `SHRIEK_MS_BIAS == 15`, `BURST_ALGO in clamps.ALLOWED_ALGOS`, `WEB_SAMPLE_HZ / MIC_FFT_SIZE == pytest.approx(23.4375)` |
| MD-02 | math: `mic_diff(-20.0, -30.0) == pytest.approx(5.5)`; `mic_diff(-20.0, -30.0, alpha=1.0) == pytest.approx(10.0)`; `mic_diff(0.0, -30.0) == pytest.approx(25.5)`; result is `float` and has ≤ 3 decimals (`mic_diff(-20.12345, -30.98765) == round(-20.12345 - 0.85 * -30.98765, 3)`) |
| MD-03 | passthrough: `mic_diff(-20.0, None) == -20.0`; `mic_diff(-20.0, "x") == -20.0`; `mic_diff(-20.0, -30.0, alpha=0.0) == -20.0`; `mic_diff(None, -30.0) == pytest.approx(25.5)`; `mic_diff(float("nan"), -30.0) == pytest.approx(25.5)`; `mic_diff_from_telemetry({"micDiff": 7.25, "micEnergy": -20, "outLevel": -30}) == 7.25`; `mic_diff_from_telemetry({"micEnergy": -20, "outLevel": -30}) == pytest.approx(5.5)`; `mic_diff_from_telemetry({"outLevel": -30}) is None`; `mic_diff_from_telemetry({}) is None` |
| MD-04 | calibration recovers α: `rng = random.Random(25)`; 20 pairs `out = -40 + 30·rng.random()`, `mic = 0.85·out + rng.gauss(0, 0.5)`; `r = calibrate_alpha(pairs)` → `r["ok"] is True`, `abs(r["alpha"] − 0.85) < 0.1`, `r["n"] == 20`, `0 <= r["residual_rms"] < 1.0`, `r["clamped"] is False`, `r["reason"] == "ok"`; exact-fit pairs `[(−8.5·k, −10·k) for k in 1..5]` → `r["alpha"] == pytest.approx(0.85, abs=1e-9)` and `r["residual_rms"] == pytest.approx(0.0, abs=1e-9)` |
| MD-05 | alpha clamp: pairs `[(−100, −10), (−200, −20), (−300, −30)]` (true slope 10) → `alpha == 2.0`, `clamped is True`, `reason` starts with `"alpha clamped"`, `ok is True`; pairs with slope −3 → `alpha == 0.0`, `clamped is True` |
| MD-06 | refusal: `calibrate_alpha([])`, `calibrate_alpha([(-20, -30), (-21, -31)])`, `calibrate_alpha([(-20, None), ("a", -30), (-21, -31), (-22, -32)])` (only 2 valid) all return `ok False`, `alpha == 0.85`, `residual_rms is None`, `reason` starts with `"need >= 3"`, and `n` equals the number of valid pairs (`0`, `2`, `2`); `calibrate_alpha([(-20, 0), (-21, 0), (-22, 0)])` → `ok False`, `reason == "outLevel has no variance"`, `alpha == 0.85`; input list is not mutated |
| MD-07 | monotonicity vs thr: for `md = 6.5`, `[burst_decision(md, thr_db=t)["extreme"] for t in (0, 3, 6, 6.4, 6.5, 6.6, 9, 20)]` is non-increasing and equals `[T,T,T,T,F,F,F,F]`; for `thr = 6.0`, `[burst_decision(m)["extreme"] for m in (-10, 0, 5.9, 6.0, 6.01, 10, 40)]` is non-decreasing and equals `[F,F,F,F,T,T,T]` (strict `>`) |
| MD-08 | extreme payload: `d = burst_decision(9.0, vib_class="physical")` → `d["algo"] == "shriek_chirp"`, `d["shriekMsBias"] == 15`, `d["vibClass"] == "physical"`, `"9.0" in d["reason"]`; `burst_decision(2.0)` → `algo is None`, `shriekMsBias == 0`; `burst_decision(None)["reason"] == "micDiff unavailable"`; `burst_decision(float("inf"))["extreme"] is False`; unknown `vib_class="bogus"` → `vibClass == "none"`; `list(d) == ["extreme","algo","shriekMsBias","thrDb","micDiffDb","vibClass","reason"]` |
| MD-09 | holdManual refuse: for every `md in (None, -10, 0, 6.01, 40, 1e9)` `burst_decision(md, hold_manual=True) == {"extreme": False, "algo": None, "shriekMsBias": 0, …, "reason": "holdManual — refuse"}`; `burst_decision_from_telemetry({"holdManual": True, "soundBurst": True, "extremeActive": True, "micDiff": 40})["extreme"] is False`; `burst_decision_from_telemetry({"holdManual": True, "micDiff": 40})["reason"] == "holdManual — refuse"` |
| MD-10 | telemetry flags: `burst_decision_from_telemetry({"soundBurst": True, "micEnergy": -40, "outLevel": -30})` → `extreme True`, `reason` starts with `"soundBurst/extremeActive flag"`, `micDiffDb == pytest.approx(-14.5)`; `{"extremeActive": True}` → `extreme True`, `micDiffDb is None`; `{"micEnergy": -12, "outLevel": -30}` → `extreme True` (13.5 dB); `{"micEnergy": -20, "outLevel": -30}` → `extreme False` (5.5 dB); `{"soundBurst": "yes"}` (non-bool) → `extreme False` |
| MD-11 | apply_burst_bias within clamps: base `{"schemaVersion":1,"algo":"hop","fMin":17000,"fMax":23000,"vol":8,"shriekMs":110,"rationale":"x"}` + extreme decision → copy has `algo == "shriek_chirp"`, `shriekMs == 120.0`, `rationale` ends with `"burst→shriek_chirp (+15 ms)"`, `burstBias == {"micDiffDb": 9.0, "shriekMsBias": 15}`, `fMin/fMax/vol` unchanged, and `clamps.validate_patch(out)[0] is True`; base `shriekMs 50` → `65.0`; missing `shriekMs` → `65.0`; base dict is unmodified (`copy.deepcopy` compare); non-extreme decision → output `== base` and `"burstBias" not in out` |
| MD-12 | aec_capability: for `None`, `""`, an iOS Safari UA, an iOS Chrome UA (`CriOS`), and a desktop Chrome UA: `fullAEC is False`, `path == "output-bus-subtraction"`, `alpha == 0.85`, `"#9" in nativePath`, `"docs/iphone-bluetooth.md" in docs`; `userAgentClass` is `"unknown"`, `"unknown"`, `"ios-safari"`, `"ios-chrome"`, `"other"` respectively; the returned dict does not contain the UA string (`json.dumps(out)` lacks `"Mozilla"`) |
| MD-13 | lf_capability: `lf_capability(None)` → `lfTx False, lfMic False`; `{"lfDriveCapable": True}` → `lfTx True`, `lfMic False`; `{"lfDriveCapable": True, "holdManual": True}` → `lfTx False`, `"holdManual" in reasons`; `{"lfArmed": True, "band": "10-20"}` → `lfTx True` (mirrors `priors.lf_drive_capable`); `{"lfArmed": True}` (no band) → `lfTx False`; `micBinHz == pytest.approx(23.44, abs=0.01)`, `txBinHz == pytest.approx(2.93, abs=0.01)`, `lfBandHz == [10.0, 20.0]`; every reason string starting with `"lfMic"` is present for all inputs; `lfTx` equals `priors.lf_drive_capable(t)` for 6 fixture dicts |
| MD-14 | hw_limits_report keys: `r = hw_limits_report()` → `r["issue"] == 25`, `r["status"] == "hw-limited"`, `r["blocksRedeploy"] is False`, `r["nativeCompanionIssue"] == 9`, `[l["id"] for l in r["limits"]] == ["full_aec","lf_mic","lf_tx","alpha_calibration"]`, every limit has exactly the keys `{"id","title","limitedBy","shippedPath","doc","nativePath"}` with non-empty strings, `"docs/algorithms.md" in r["docs"]` and `"docs/iphone-bluetooth.md" in r["docs"]`, `json.dumps(r)` round-trips, `hw_limits_report() == hw_limits_report()` and returns a fresh object (`is not`), `"http" not in json.dumps(r)` |
| MD-15 | honesty greps: source of `mic_diff.py` contains no `CFD`, no `Navier`, no `bluetooth.requestDevice`, no `import scipy`, no `from google`, no `os.environ`; contains `"proxy"`; `sys.modules` after `import iot_asp_autoroute.mic_diff` in a fresh subprocess lacks `scipy` and `google` |
| MD-16 | CLI demo: `subprocess.run([sys.executable, "-m", "iot_asp_autoroute.mic_diff", "--demo"], cwd="services/autoroute-adk", capture_output=True, env={**os.environ, "IOT_ASP_AUTOROUTE_DRY_RUN": "1"})` → returncode 0, stdout parses as JSON with keys `{"micDiff","calibration","burst","burstHold","aec","lf","report"}`, `out["micDiff"] == 5.5`, `abs(out["calibration"]["alpha"] − 0.85) < 0.1`, `out["burst"]["extreme"] is True`, `out["burstHold"]["reason"] == "holdManual — refuse"`, `out["aec"]["fullAEC"] is False`, `out["lf"]["lfMic"] is False`, `len(out["report"]["limits"]) == 4`; two runs produce byte-identical stdout; no-arg run exits 2 |
| MD-17 | negative controls: `burst_decision("6.5")` (string) → `extreme True` (numeric coercion) but `burst_decision("abc")["reason"] == "micDiff unavailable"`; `apply_burst_bias(patch, {"extreme": True, "shriekMsBias": 999, "micDiffDb": 9})` → `shriekMs == 120.0` (clamp wins over a bogus bias); `apply_burst_bias({"algo": "hop"}, {})` returns `{"algo": "hop"}`; `lf_capability({"lfDriveCapable": "true"})` (string, not bool) → `lfTx False` (matches `priors.lf_drive_capable` strict `is True`) |

**Implementation deltas (as shipped — the table above remains binding, these are additions):**

- `lf_capability()["reasons"]` carries a **third** `lfMic:` line, `"lfMic: lfEnergy is the LF accelerometer
  felt proxy, not infrasound capture"`, so the honesty statement is on the wire as well as in the source.
- `burst_decision_from_telemetry` flag reason is `"soundBurst/extremeActive flag; <underlying micDiff
  reason>"` (still starts with `"soundBurst/extremeActive flag"`).
- `apply_burst_bias` always uses the module constant `SHRIEK_MS_BIAS` (15) for both `shriekMs` and
  `burstBias.shriekMsBias`; a bogus `decision["shriekMsBias"]` is ignored (MD-17).
- `demo()["burst"]` is the extreme decision for `micEnergy −12 / outLevel −30` (13.5 dB) plus two extra
  keys `quietMicDiffDb` (5.5) and `quietExtreme` (`False`) documenting the non-extreme case; the top-level
  demo key set is exactly `{micDiff, calibration, burst, burstHold, aec, lf, report}`.
- MD-15 subprocess check imports the package first, then diffs `sys.modules` around
  `import iot_asp_autoroute.mic_diff`, so it stays valid when `google-adk` is installed (the package
  `__init__` soft-imports `agent` → `tools` → `vib_anomaly` → scipy in that environment).
- `mic_diff(..., alpha=<non-finite>)` and `burst_decision(..., thr_db=<non-numeric>)` fall back to the
  module defaults (`0.85`, `6.0`) rather than raising; booleans are never treated as levels.

## CI gate

- `tests` job (`python3 -m pytest tests -q`) picks up `tests/test_mic_diff.py`; numpy is in
  `requirements-dev.txt` and `services/autoroute-adk/requirements.txt` already — no new dependency.
- `autoroute` job: `bash scripts/autoroute_dev.sh` stays green (module is not on the dry-run path until
  the integrator hook lands; after it lands the dry-run telemetry has no burst keys → no bias → same
  output). Suggested import smoke for `ci.yml` (integrator): `python3 -c "import
  iot_asp_autoroute.mic_diff as m; assert m.MIC_DIFF_ALPHA == 0.85 and
  m.burst_decision(40, hold_manual=True)['extreme'] is False"`.
- `static_gates`: no change (nothing under `public/`).
- `pr_issue_ref`: PR body carries `Related: #25` (this issue must not be `Fixes`-closed — it stays open
  as the HW-limited tracker until #9 lands).

## Risks / HW limits

The four leftovers from the issue, restated as facts the module encodes (`hw_limits_report`):

| # | Limit | Why (cited) | Shipped mitigation | Fuller path |
|---|-------|-------------|--------------------|-------------|
| 1 | **Full AEC** on iOS Safari / Chrome Web Audio | Browser `echoCancellation` is a speech-mode processor; the page must set it `false` or the 20 kHz carrier is destroyed (`public/index.html:937-944`). Constraints are advisory — user agents ignore constraints they do not honour (MDN `MediaTrackConstraints.echoCancellation`), and WebKit has open history of the constraint not taking effect (bugs.webkit.org 179411) and of VPIO being instantiated regardless (webkit/webkit#70443). iOS Chrome uses the same WebKit engine. There is no web API for carrier-band AEC. | `micDiff = micEnergy − α·outLevel` output-bus subtraction, α = 0.85 default, `calibrate_alpha` per route | Native companion (#9): `AVAudioSession` voice-processing / custom AEC on the raw bus; HFP only if mic-on-speaker is elected (`docs/iphone-bluetooth.md:30-37`) |
| 2 | **LF mic** (< 20 Hz) | Consumer mics / BT high-pass (`docs/algorithms.md:29`); mic analyser `fftSize 2048` at 48 kHz gives 23.44 Hz/bin (MDN: bins are linear from 0 to Nyquist, count = `fftSize/2`), so everything below 20 Hz lands in bin 0 with DC. `lfEnergy` is therefore the **accelerometer felt proxy**, not infrasound capture. | `lf_capability()["lfMic"] is False`; `lfEnergy` semantics documented as proxy | Dedicated infrasound mic / geophone on native hardware — parked (`docs/algorithms.md:31`) |
| 3 | **LF TX 10–20 Hz** | Soundcore 2 + A2DP/BassUp DSP roll off; typical A2DP route is "na" (issue). | `lfTx = priors.lf_drive_capable(t)`; band `10-20` only via `priors.band_for_telemetry` + `clamps.band_limits` when `lfDriveCapable` | Node-3 / phone-speaker experiment (#18); `lfDriveCapable` stays `false` for the web fleet by default (`docs/api-contract.md:83`) |
| 4 | **α calibration** per device / BT route | α depends on codec (AAC/SBC), speaker DSP and room; a single 0.85 is a fleet default. | `calibrate_alpha` — least squares through origin, `[0, 2]` clamp, refuses `< 3` pairs; result is **advisory** until the integrator persists it (not in this item) | Per-route AEC in the native shell (#9) |

Additional risks:

- **`micEnergy` units.** The contract stores `micEnergy` "as sent (dB or linear)". `mic_diff` assumes
  dB for both operands; a linear `micEnergy` (≤ 1) with a dB `outLevel` gives a meaningless positive
  `micDiff` (e.g. `0.03 − 0.85·(−30) = 25.5 dB` → false burst). Mitigation in this item: the phone value
  `micDiff` wins when present, and `burst_decision_from_telemetry` is only wired by the integrator after
  the beacon emits `outLevel` in dB. Documented, not silently corrected.
- **Calibration set contamination.** Pairs captured while an environmental burst is present bias α upward
  and are clamped at 2.0; the `ok`/`clamped`/`residual_rms` fields let the caller reject the fit. Callers
  must only feed pairs with `soundBurst` false.
- **Rank-deficient design.** `outLevel` all zero → `lstsq` returns an empty residual array and `rank 0`;
  the module refuses explicitly instead of returning α = 0 (NumPy docs: residuals empty when rank < N).
- **UA sniffing is not capability detection.** `userAgentClass` is informational; `fullAEC` does not
  depend on it, so a spoofed UA cannot unlock anything.
- **Concurrent edits.** `sudden_freq.py` / `tools.py` / `agent.py` are integrator-owned; the hook is a
  4-line additive block after the existing duty bias so merges stay mechanical.

## Sources

- Context7 `/mdn/content` — `MediaTrackConstraints.echoCancellation` / `noiseSuppression` /
  `autoGainControl` ("browsers will ignore any constraints they're unfamiliar with";
  `MediaDevices.getSupportedConstraints()` for support checks) —
  https://developer.mozilla.org/en-US/docs/Web/API/MediaTrackConstraints/echoCancellation
- Context7 `/mdn/content` — `AnalyserNode.fftSize`, `frequencyBinCount` (= `fftSize / 2`, linear from 0 to
  Nyquist), `getFloatFrequencyData` (dB values, 0 … sampleRate/2) —
  https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode/frequencyBinCount
- Context7 `/websites/numpy_doc_stable` — `numpy.linalg.lstsq(a, b, rcond=None)` returns
  `(x, residuals, rank, s)`; residuals are the squared 2-norm and are **empty when rank < N or M <= N** —
  https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html (numpy 2.4.6 installed here;
  pin `numpy>=1.26.0,<3` in `services/autoroute-adk/requirements.txt`)
- Firecrawl developer search — https://bugs.webkit.org/show_bug.cgi?id=179411 ("getUserMedia
  echoCancellation constraint has no affect"); https://github.com/webkit/webkit/issues/70443
  (`getUserMedia` with `echoCancellation:false` still instantiates VPIO system-wide; fix computes
  `willUseEchoCancellation` from constraints); https://github.com/webaudio/web-audio-api/issues/1187
  (Web Audio amplitude drift unless `echoCancellation:false`).
- Re-verified at implementation time (2026-09-08): Context7 `/websites/numpy_doc_stable` `numpy.linalg.lstsq`
  ("Residuals are returned as an empty array if the rank of `a` is less than N or M <= N") — basis for
  the rank-0 refusal; Context7 `/mdn/content` `MediaTrackConstraints.echoCancellation` ("browsers will
  ignore any constraints they're unfamiliar with") and `MediaTrackSupportedConstraints.echoCancellation`;
  Firecrawl developer search — webkit/webkit PR #14490 / https://bugs.webkit.org/show_bug.cgi?id=257495
  ("Set echoCancellation to true if not explicitly set within a getUserMedia call" — WebKit defaults the
  speech-mode processor **on**, so the page must pass `false` explicitly).
- GitHub issue #25 (scope, "Do not block public hop redeploys"), #9 (native/Xcode shell), #18
  (phone-speaker LF), #26 (`micDiff`/`shriekBias` consumer) — read via the GitHub connector on 2026-09-08.
- Repo (file:line cites above): `docs/api-contract.md`, `docs/DESIGN_CONSTRAINTS.md`,
  `docs/iphone-bluetooth.md`, `docs/algorithms.md`, `docs/autoroute.md`, `docs/ci.md`,
  `docs/specs/26-colab-live-gcs-features.md`, `services/autoroute-adk/iot_asp_autoroute/{clamps,priors,
  sudden_freq,tools,agent,vib_anomaly}.py`, `public/index.html`, `CLAUDE.md`, `.claude/rules/*.md`.
- Literature (constraints only, IDs from `reference/LITERATURE.md` via `priors.py:43-74`):
  `doi:10.1121/1.5063819` (VHFS/US exposure ethics — not a medical claim), `doi:10.1121/10.0003509`
  (felt < 20 Hz context). No new citations introduced.
