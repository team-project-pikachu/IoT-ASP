"""HW-limited LF mic/TX + best-effort AEC ``micDiff`` helpers (issue #25).

Honest backend side of the four hardware leftovers in #25:

* full AEC on iOS web audio is **not** available — the page must disable the
  browser's speech-mode ``echoCancellation`` or the 20 kHz carrier is destroyed,
  and the constraint is advisory (browsers ignore constraints they do not honour,
  MDN ``MediaTrackConstraints.echoCancellation``); what ships is output-bus
  subtraction ``micDiff = micEnergy - alpha * outLevel`` (``docs/api-contract.md``);
* an LF (<20 Hz) **mic** is not available — consumer mic/BT high-pass plus the
  2048-point mic analyser at 48 kHz (23.44 Hz/bin) leave everything below 20 Hz in
  bin 0; ``lfEnergy`` is the accelerometer *felt proxy* (``docs/algorithms.md``);
* LF **TX** 10–20 Hz exists only when telemetry asserts ``lfDriveCapable``
  (``priors.lf_drive_capable``); the A2DP/Soundcore route rolls off;
* ``alpha`` depends on device + BT route — ``calibrate_alpha`` fits it from TX-only
  pairs (least squares through the origin, clamped, refusing tiny sets).

Everything here is pure, offline and deterministic: stdlib + numpy (only in
``calibrate_alpha``); no scipy, no GCS, no env reads. Hold / Manual always wins.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import random
import sys
from typing import Any, Iterable

from .clamps import ALLOWED_ALGOS, CLAMPS, validate_patch
from .priors import LF_BAND_HZ, lf_drive_capable, normalize_vib_class

# ── constants (asserted by tests/test_mic_diff.py) ───────────────────────────

MIC_DIFF_ALPHA = 0.85  # output-bus subtraction weight (docs/api-contract.md micDiff row)
MIC_DIFF_THR_DB = 6.0  # burst threshold on micDiff (matches #26 shriekBias)
ALPHA_RANGE = (0.0, 2.0)  # calibration clamp
MIN_CAL_PAIRS = 3  # below this calibrate_alpha refuses
SHRIEK_MS_BIAS = 15  # added to shriekMs on a burst, then clamped to CLAMPS["shriekMs"]
BURST_ALGO = "shriek_chirp"  # wire name

# Mirrors public/index.html: micAnalyser.fftSize = 2048, TX analyser.fftSize = 16384,
# preferred AudioContext sampleRate 48000 (docs/iphone-bluetooth.md).
MIC_FFT_SIZE = 2048
TX_FFT_SIZE = 16384
WEB_SAMPLE_HZ = 48000

HOLD_REFUSE = "holdManual — refuse"
_NATIVE_AEC_PATH = "#9 AVAudioSession / HFP (docs/iphone-bluetooth.md)"

assert BURST_ALGO in ALLOWED_ALGOS, BURST_ALGO


# ── helpers ──────────────────────────────────────────────────────────────────


def _finite(value: Any) -> float | None:
    """Coerce to a finite float; ``None`` for None / non-numeric / nan / inf / bool."""
    if value is None or isinstance(value, bool):
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return f


def _clamp(lo: float, hi: float, value: float) -> float:
    return max(lo, min(hi, value))


# ── micDiff ──────────────────────────────────────────────────────────────────


def mic_diff(
    mic_energy_db: Any,
    out_level_db: Any,
    alpha: Any = MIC_DIFF_ALPHA,
) -> float:
    """Best-effort AEC: ``round(mic - alpha * out, 3)``.

    Non-finite / missing operands coerce to ``0.0`` (a missing ``outLevel`` is a
    passthrough: ``micDiff == micEnergy``). ``alpha`` None/non-finite → default.
    Never raises.
    """
    mic = _finite(mic_energy_db)
    out = _finite(out_level_db)
    a = _finite(alpha)
    if a is None:
        a = MIC_DIFF_ALPHA
    return round((mic or 0.0) - a * (out or 0.0), 3)


def mic_diff_from_telemetry(t: dict[str, Any] | None, alpha: Any = None) -> float | None:
    """Phone value wins when finite; else derive from ``micEnergy``/``outLevel``; else None."""
    if not t:
        return None
    given = _finite(t.get("micDiff"))
    if given is not None:
        return given
    mic = _finite(t.get("micEnergy"))
    if mic is None:
        return None
    a = _finite(alpha)
    return mic_diff(mic, t.get("outLevel"), a if a is not None else MIC_DIFF_ALPHA)


# ── calibration ──────────────────────────────────────────────────────────────


def _refusal(n: int, reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "alpha": MIC_DIFF_ALPHA,
        "n": n,
        "residual_rms": None,
        "clamped": False,
        "reason": reason,
    }


def calibrate_alpha(pairs: Iterable[Any]) -> dict[str, Any]:
    """Least-squares ``alpha`` (through the origin) from TX-only ``(micEnergy, outLevel)`` pairs.

    Pairs must be captured with the carrier playing and no environmental burst
    (``soundBurst`` false). Result is advisory: callers must not persist ``alpha``
    when ``ok`` is false. ``alpha`` is clamped to ``ALPHA_RANGE``; fewer than
    ``MIN_CAL_PAIRS`` valid pairs, or an ``outLevel`` column with no variance,
    refuses with the default.
    """
    mic_vals: list[float] = []
    out_vals: list[float] = []
    for pair in pairs:
        try:
            m_raw, o_raw = pair
        except (TypeError, ValueError):
            continue
        m, o = _finite(m_raw), _finite(o_raw)
        if m is None or o is None:
            continue
        mic_vals.append(m)
        out_vals.append(o)
    n = len(mic_vals)
    if n < MIN_CAL_PAIRS:
        return _refusal(n, f"need >= {MIN_CAL_PAIRS} TX-only pairs, got {n}")

    import numpy as np  # numpy allowed by the brief; imported lazily (stdlib-first module)

    out = np.asarray(out_vals, dtype=float)
    mic = np.asarray(mic_vals, dtype=float)
    # M×1 design matrix → rank 1 unless outLevel is all zero (rank 0, residuals empty).
    sol, _resid, rank, _sv = np.linalg.lstsq(out[:, None], mic, rcond=None)
    if int(rank) < 1:
        return _refusal(n, "outLevel has no variance")
    alpha_raw = float(sol[0])
    alpha = _clamp(ALPHA_RANGE[0], ALPHA_RANGE[1], alpha_raw)
    clamped = alpha != alpha_raw
    residual_rms = float(np.sqrt(np.mean((mic - alpha * out) ** 2)))
    return {
        "ok": True,
        "alpha": round(alpha, 4),
        "n": n,
        "residual_rms": round(residual_rms, 4),
        "clamped": clamped,
        "reason": f"alpha clamped from {round(alpha_raw, 4)}" if clamped else "ok",
    }


# ── capability answers ───────────────────────────────────────────────────────


def _ua_class(user_agent: str | None) -> str:
    ua = (user_agent or "").strip()
    if not ua:
        return "unknown"
    ios = "iPhone" in ua or "iPad" in ua
    if "CriOS" in ua and ios:
        return "ios-chrome"
    if ios and "Safari" in ua:
        return "ios-safari"
    return "other"


def aec_capability(user_agent: str | None = None) -> dict[str, Any]:
    """Can this web fleet do full AEC on a 20 kHz carrier? Always no.

    Browser ``echoCancellation`` is a speech-mode processor the page disables
    (``public/index.html`` mic constraints); the constraint is advisory (MDN) and
    no web API cancels a carrier-band echo. The UA string is classified and
    discarded — it never unlocks anything.
    """
    ua_class = _ua_class(user_agent)
    return {
        "fullAEC": False,
        "path": "output-bus-subtraction",
        "alpha": MIC_DIFF_ALPHA,
        "userAgentClass": ua_class,
        "reason": (
            "browser echoCancellation is a speech-mode processor that annihilates a "
            "20 kHz carrier, so the page requests echoCancellation:false; constraints "
            "are advisory (user agents ignore constraints they do not honour), and no "
            "web API exposes carrier-band AEC on iOS Safari/Chrome (WebKit) — "
            f"userAgentClass={ua_class} does not change this"
        ),
        "nativePath": _NATIVE_AEC_PATH,
        "docs": ["docs/iphone-bluetooth.md", "docs/api-contract.md"],
    }


def lf_capability(telemetry: dict[str, Any] | None) -> dict[str, Any]:
    """LF (10–20 Hz) capability: TX gated by ``priors.lf_drive_capable``; mic never."""
    t = telemetry or {}
    lf_tx = lf_drive_capable(t)
    mic_bin = round(WEB_SAMPLE_HZ / MIC_FFT_SIZE, 2)
    tx_bin = round(WEB_SAMPLE_HZ / TX_FFT_SIZE, 2)
    reasons = [
        "lfMic: consumer mic/BT high-pass (docs/algorithms.md § Infrasound honesty)",
        f"lfMic: micAnalyser fftSize {MIC_FFT_SIZE} @ 48 kHz -> {mic_bin} Hz/bin; <20 Hz is bin 0",
        "lfMic: lfEnergy is the LF accelerometer felt proxy, not infrasound capture",
    ]
    if lf_tx:
        reasons.append("lfTx: lfDriveCapable asserted by telemetry")
    else:
        reasons.append("lfTx: gated by lfDriveCapable (priors.lf_drive_capable)")
    if t.get("holdManual"):
        reasons.append("holdManual")
    return {
        "lfTx": bool(lf_tx),
        "lfMic": False,
        "micBinHz": mic_bin,
        "txBinHz": tx_bin,
        "lfBandHz": [float(LF_BAND_HZ[0]), float(LF_BAND_HZ[1])],
        "reasons": reasons,
    }


# ── burst decision ───────────────────────────────────────────────────────────


def _decision(
    *,
    extreme: bool,
    thr_db: float,
    mic_diff_db: float | None,
    vib_class: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "extreme": bool(extreme),
        "algo": BURST_ALGO if extreme else None,
        "shriekMsBias": SHRIEK_MS_BIAS if extreme else 0,
        "thrDb": thr_db,
        "micDiffDb": mic_diff_db,
        "vibClass": vib_class,
        "reason": reason,
    }


def burst_decision(
    mic_diff_db: Any,
    thr_db: Any = MIC_DIFF_THR_DB,
    hold_manual: bool = False,
    vib_class: str | None = None,
) -> dict[str, Any]:
    """Turn ``micDiff`` into a burst → ``shriek_chirp`` bias. Refuses under Hold / Manual."""
    vib = normalize_vib_class(vib_class)
    thr = _finite(thr_db)
    if thr is None:
        thr = MIC_DIFF_THR_DB
    md = _finite(mic_diff_db)
    if hold_manual:
        return _decision(extreme=False, thr_db=thr, mic_diff_db=md, vib_class=vib, reason=HOLD_REFUSE)
    if md is None:
        return _decision(extreme=False, thr_db=thr, mic_diff_db=None, vib_class=vib, reason="micDiff unavailable")
    if md > thr:
        return _decision(
            extreme=True,
            thr_db=thr,
            mic_diff_db=md,
            vib_class=vib,
            reason=f"micDiff {md} dB > thr {thr} dB; vibClass={vib}",
        )
    return _decision(extreme=False, thr_db=thr, mic_diff_db=md, vib_class=vib, reason=f"micDiff {md} dB <= thr {thr} dB")


def burst_decision_from_telemetry(t: dict[str, Any] | None, thr_db: Any = MIC_DIFF_THR_DB) -> dict[str, Any]:
    """Burst decision from a telemetry dict: ``holdManual`` first, then phone flags, then ``micDiff``."""
    t = t or {}
    hold = bool(t.get("holdManual"))
    md = mic_diff_from_telemetry(t)
    vib = t.get("vibClass")
    if not hold and (t.get("soundBurst") is True or t.get("extremeActive") is True):
        thr = _finite(thr_db)
        base = burst_decision(md, thr if thr is not None else MIC_DIFF_THR_DB, False, vib)
        return _decision(
            extreme=True,
            thr_db=base["thrDb"],
            mic_diff_db=md,
            vib_class=base["vibClass"],
            reason=f"soundBurst/extremeActive flag; {base['reason']}",
        )
    return burst_decision(md, thr_db, hold, vib)


BIAS_REFUSE_PREFIX = "refuse burst bias: "


def burst_bias_eligibility(patch: Any) -> tuple[bool, str]:
    """May ``apply_burst_bias`` touch this patch? Only when it already validates.

    ``clamps.validate_patch`` is the single source of truth for policy; a draft it
    refuses (``shriekMs`` outside ``CLAMPS['shriekMs']`` or non-numeric, ``algo``
    off the whitelist, band / ``vol`` violations …) is **refused, never rewritten**
    into policy by the bias (CLAUDE.md invariant 5). Returns ``(ok, reason)`` where
    ``reason`` carries ``validate_patch``'s own message on refusal.
    """
    if not isinstance(patch, dict):
        return False, f"{BIAS_REFUSE_PREFIX}patch is not a dict"
    ok, msg, _clamped = validate_patch(patch)
    if not ok:
        return False, f"{BIAS_REFUSE_PREFIX}{msg}"
    return True, "ok"


def apply_burst_bias(patch: dict[str, Any], decision: dict[str, Any] | None) -> dict[str, Any]:
    """Return a copy of ``patch`` biased toward ``shriek_chirp`` when ``decision['extreme']``.

    The bias is applied **only** to a patch that ``clamps.validate_patch`` already
    accepts (``burst_bias_eligibility``). An out-of-policy draft — ``shriekMs``
    outside ``CLAMPS['shriekMs']`` / non-numeric, ``algo`` off the whitelist, … —
    comes back as an unchanged copy (no ``algo`` swap, no ``burstBias``), so the
    caller's mandatory ``validate_patch`` still refuses it with its own message:
    refuse, never silently rewrite. On an eligible patch only the **+15 ms delta**
    is clamped to ``CLAMPS['shriekMs']`` (``110 + 15 → 120``). Never touches
    ``vol``, ``fMin``, ``fMax`` or ``band``.
    """
    out = copy.deepcopy(patch)
    if not decision or not decision.get("extreme"):
        return out
    eligible, _reason = burst_bias_eligibility(out)
    if not eligible:
        return out
    lo, hi = CLAMPS["shriekMs"]
    base = _finite(out.get("shriekMs"))  # eligible ⇒ absent/None or finite inside [lo, hi]
    if base is None:
        base = 50.0
    out["algo"] = BURST_ALGO
    out["shriekMs"] = _clamp(lo, hi, base + SHRIEK_MS_BIAS)
    note = f"burst→{BURST_ALGO} (+{SHRIEK_MS_BIAS} ms)"
    rationale = str(out.get("rationale") or "")
    out["rationale"] = f"{rationale}; {note}" if rationale else note
    out["burstBias"] = {"micDiffDb": decision.get("micDiffDb"), "shriekMsBias": SHRIEK_MS_BIAS}
    return out


# ── HW-limited report ────────────────────────────────────────────────────────

_LIMITS: tuple[dict[str, str], ...] = (
    {
        "id": "full_aec",
        "title": "Full AEC on iOS Safari / Chrome Web Audio",
        "limitedBy": (
            "browser echoCancellation is a speech-mode processor that destroys the "
            "20 kHz carrier; the page disables it and the constraint is advisory; no "
            "web API for carrier-band AEC"
        ),
        "shippedPath": f"output-bus subtraction micDiff = micEnergy - {MIC_DIFF_ALPHA}*outLevel (mic_diff)",
        "doc": "docs/iphone-bluetooth.md",
        "nativePath": "#9 AVAudioSession voice-processing / custom AEC on the raw bus",
    },
    {
        "id": "lf_mic",
        "title": "LF (<20 Hz) microphone capture",
        "limitedBy": (
            f"consumer mic/BT high-pass; micAnalyser fftSize {MIC_FFT_SIZE} @ 48 kHz "
            f"= {round(WEB_SAMPLE_HZ / MIC_FFT_SIZE, 2)} Hz/bin so <20 Hz is bin 0"
        ),
        "shippedPath": "lfEnergy = LF accelerometer felt proxy (lf_capability lfMic=False)",
        "doc": "docs/algorithms.md § Infrasound honesty",
        "nativePath": "dedicated infrasound mic / geophone on native hardware — parked",
    },
    {
        "id": "lf_tx",
        "title": "LF TX 10-20 Hz over A2DP",
        "limitedBy": "Soundcore 2 + A2DP/BassUp DSP roll-off; typical A2DP route cannot drive 10-20 Hz",
        "shippedPath": "band 10-20 only when priors.lf_drive_capable(telemetry) (lfDriveCapable)",
        "doc": "docs/algorithms.md",
        "nativePath": "#18 Node-3 / phone-speaker LF experiment; #9 native shell",
    },
    {
        "id": "alpha_calibration",
        "title": "alpha calibration per device / BT route",
        "limitedBy": "alpha depends on codec (AAC/SBC), speaker DSP and room; 0.85 is a fleet default",
        "shippedPath": "calibrate_alpha from TX-only pairs (least squares through origin, [0, 2] clamp, refuses < 3 pairs)",
        "doc": "docs/specs/25-hw-limited-lf-aec-micdiff.md",
        "nativePath": "#9 per-route AEC in the native shell",
    },
)


def hw_limits_report() -> dict[str, Any]:
    """The four HW-limited leftovers of #25 (never blocks public hop redeploys)."""
    return {
        "issue": 25,
        "status": "hw-limited",
        "blocksRedeploy": False,
        "nativeCompanionIssue": 9,
        "relatedIssues": [9, 18, 26],
        "docs": [
            "docs/algorithms.md",
            "docs/iphone-bluetooth.md",
            "docs/api-contract.md",
            "docs/specs/25-hw-limited-lf-aec-micdiff.md",
        ],
        "limits": [dict(limit) for limit in _LIMITS],
    }


# ── demo / CLI ───────────────────────────────────────────────────────────────

_DEMO_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"


def demo() -> dict[str, Any]:
    """Deterministic offline demo (seed 25)."""
    rng = random.Random(25)
    pairs = []
    for _ in range(12):
        out = -40.0 + 30.0 * rng.random()
        pairs.append((MIC_DIFF_ALPHA * out + rng.gauss(0.0, 0.5), out))
    quiet = burst_decision(mic_diff(-20.0, -30.0))  # 5.5 dB → not extreme
    burst = burst_decision(mic_diff(-12.0, -30.0), vib_class="acoustic")  # 13.5 dB → extreme
    burst["quietMicDiffDb"] = quiet["micDiffDb"]
    burst["quietExtreme"] = quiet["extreme"]
    return {
        "micDiff": mic_diff(-20.0, -30.0),
        "calibration": calibrate_alpha(pairs),
        "burst": burst,
        "burstHold": burst_decision(20.0, hold_manual=True),
        "aec": aec_capability(_DEMO_UA),
        "lf": lf_capability({"lfDriveCapable": False}),
        "report": hw_limits_report(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m iot_asp_autoroute.mic_diff",
        description="HW-limited LF/AEC micDiff helpers (#25) — offline demo.",
    )
    parser.add_argument("--demo", action="store_true", help="print the deterministic demo JSON")
    args = parser.parse_args(argv)
    if not args.demo:
        parser.print_usage(sys.stderr)
        return 2
    print(json.dumps(demo(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
