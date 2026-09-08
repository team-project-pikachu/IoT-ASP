"""Authoritative vibration / disturbance anomaly detection via SciPy.

Browser Chrome iOS only ingests DeviceMotion and beacons 1 Hz samples.
This module is the authoritative detector (median filter + MAD z-score + peaks).

Units: vib series is acceleration magnitude in **g** (DeviceMotion convention).
Quantum: outputs rounded to nearest **0.0005 g**.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    from scipy.signal import find_peaks, medfilt
    from scipy.stats import median_abs_deviation
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "scipy is required for vib_anomaly; pin scipy in requirements.txt"
    ) from exc

VIB_QUANTUM = 0.0005  # g
DEFAULT_Z_THRESH = 3.5
DEFAULT_MEDFILT_KERNEL = 5  # odd
DEFAULT_MIN_BASELINE = 8  # samples before MAD is trusted


def quantize_vib(x: float, quantum: float = VIB_QUANTUM) -> float:
    """Round to nearest quantum (default 0.0005 g)."""
    if not np.isfinite(x):
        return 0.0
    q = float(quantum)
    if q <= 0:
        return float(x)
    return round(float(x) / q) * q


def quantize_series(series: np.ndarray, quantum: float = VIB_QUANTUM) -> np.ndarray:
    arr = np.asarray(series, dtype=float)
    return np.vectorize(lambda v: quantize_vib(v, quantum))(arr)


def _ensure_odd(k: int) -> int:
    k = max(1, int(k))
    return k if k % 2 == 1 else k + 1


def detect_disturbances(
    vib_series: list[float] | np.ndarray,
    *,
    quantum: float = VIB_QUANTUM,
    z_thresh: float = DEFAULT_Z_THRESH,
    medfilt_kernel: int = DEFAULT_MEDFILT_KERNEL,
    min_baseline: int = DEFAULT_MIN_BASELINE,
    sample_hz: float = 1.0,
) -> dict[str, Any]:
    """Run SciPy anomaly detection on a vib magnitude series (g).

    Pipeline:
      1. Quantize to ``quantum`` (0.0005 g).
      2. ``scipy.signal.medfilt`` baseline.
      3. Residual = vibQ − baseline; MAD via ``scipy.stats.median_abs_deviation``.
      4. Flag when |residual| / (1.4826·MAD) ≥ z_thresh **or** quantized |Δ| steps ≥ 1
         past rolling MAD floor (at least one 0.0005 step above noise).
      5. ``scipy.signal.find_peaks`` on |residual| for peak indices.

    Returns dict with vib, vibQ, baseline, anomaly (bool per sample), peaks, meta.
    """
    raw = np.asarray(vib_series, dtype=float).ravel()
    n = int(raw.size)
    if n == 0:
        return {
            "ok": True,
            "n": 0,
            "vib": [],
            "vibQ": [],
            "baseline": [],
            "anomaly": [],
            "peaks": [],
            "disturbance": False,
            "quantum": quantum,
            "sampleHz": sample_hz,
            "engine": "scipy",
            "functions": [
                "scipy.signal.medfilt",
                "scipy.stats.median_abs_deviation",
                "scipy.signal.find_peaks",
            ],
        }

    vib_q = quantize_series(raw, quantum)
    k = _ensure_odd(medfilt_kernel)
    if n < k:
        baseline = np.full(n, float(np.median(vib_q)))
    else:
        baseline = medfilt(vib_q, kernel_size=k)
    baseline = quantize_series(baseline, quantum)

    resid = vib_q - baseline
    anomaly = np.zeros(n, dtype=bool)

    if n >= min_baseline:
        # scale='normal' → consistent σ estimator (SciPy docs /scipy/scipy)
        mad = float(median_abs_deviation(resid, scale="normal", nan_policy="omit"))
        scale = mad if mad > 0 else quantum
        z = np.abs(resid) / scale
        # Also require at least one quantum step from baseline when MAD collapses
        quantum_steps = np.round(np.abs(resid) / quantum)
        anomaly = (z >= z_thresh) & (quantum_steps >= 1)
        if mad <= 0:
            anomaly = quantum_steps >= 2  # two quanta when flat baseline
    else:
        mad = 0.0
        # Warm-up: flag only large absolute jumps (≥ 4 quanta)
        anomaly = np.round(np.abs(np.diff(vib_q, prepend=vib_q[0])) / quantum) >= 4

    height = max(quantum * 2, float(np.percentile(np.abs(resid), 75)) if n > 4 else quantum * 2)
    peaks, _props = find_peaks(np.abs(resid), height=height, distance=max(1, int(sample_hz)))

    return {
        "ok": True,
        "n": n,
        "vib": [float(v) for v in raw],
        "vibQ": [float(v) for v in vib_q],
        "baseline": [float(v) for v in baseline],
        "anomaly": [bool(a) for a in anomaly],
        "peaks": [int(i) for i in peaks],
        "disturbance": bool(np.any(anomaly)),
        "last": {
            "vib": float(raw[-1]),
            "vibQ": float(vib_q[-1]),
            "baseline": float(baseline[-1]),
            "anomaly": bool(anomaly[-1]),
            "deltaQ": quantize_vib(float(resid[-1]), quantum),
        },
        "mad": mad,
        "zThresh": z_thresh,
        "quantum": quantum,
        "sampleHz": sample_hz,
        "units": "g",
        "engine": "scipy",
        "functions": [
            "scipy.signal.medfilt",
            "scipy.stats.median_abs_deviation",
            "scipy.signal.find_peaks",
        ],
    }


def synthetic_demo_series(n: int = 60, seed: int = 42) -> list[float]:
    """1 Hz synthetic vib (g) with two injected spikes for dry-run."""
    rng = np.random.default_rng(seed)
    base = 0.02 + 0.002 * rng.standard_normal(n)
    base = np.clip(base, 0.0, None)
    if n > 20:
        base[20] += 0.08
    if n > 45:
        base[45] += 0.12
    return [float(quantize_vib(v)) for v in base]


def detect_from_telemetry_points(points: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract vib/absA/a from telemetry JSON list (1 Hz preferred) and detect."""
    series: list[float] = []
    for p in points:
        v = p.get("vib")
        if v is None:
            v = p.get("vibQ")
        if v is None:
            v = p.get("absA", p.get("a"))
        if v is None:
            continue
        try:
            series.append(float(v))
        except (TypeError, ValueError):
            continue
    out = detect_disturbances(series)
    out["source"] = "telemetry_points"
    out["pointCount"] = len(points)
    return out
