"""≥16-parameter nonlinear diurnal circle fit via SciPy curve_fit."""

from __future__ import annotations

from typing import Any

import numpy as np

from .weather import fairfax_weather_prior, weather_bias

try:
    from scipy.optimize import curve_fit
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "scipy is required for algo_timestore.fit; pin scipy in packages/algo-timestore/requirements.txt"
    ) from exc

# Mean + 7 harmonic pairs (cos/sin) + year drift = 16 parameters.
N_HARMONICS = 7
N_PARAMS = 1 + 2 * N_HARMONICS + 1  # 16
assert N_PARAMS >= 16


def model_circle(circle_frac: np.ndarray, *params: float) -> np.ndarray:
    """Diurnal Fourier series + mild year-fraction drift.

    ``circle_frac`` ∈ [0, 1). ``params`` length must be ``N_PARAMS``.
    Year drift uses ``params[-1]`` against mean(circle) as a soft seasonal proxy
    when a separate year series is not supplied (MVP).
    """
    p = np.asarray(params, dtype=float).ravel()
    if p.size != N_PARAMS:
        raise ValueError(f"expected {N_PARAMS} params, got {p.size}")
    x = np.asarray(circle_frac, dtype=float).ravel()
    y = np.full_like(x, p[0], dtype=float)
    for k in range(1, N_HARMONICS + 1):
        a = p[2 * k - 1]
        b = p[2 * k]
        ang = 2.0 * np.pi * k * x
        y = y + a * np.cos(ang) + b * np.sin(ang)
    # Soft seasonal tilt vs mean circle position (MVP stand-in for year horizon).
    y = y + p[-1] * (x - 0.5)
    return y


def _default_p0() -> np.ndarray:
    p0 = np.zeros(N_PARAMS, dtype=float)
    p0[0] = 1.0
    p0[1] = 0.15
    p0[2] = 0.05
    return p0


def fit_circle_series(
    circle_frac: list[float] | np.ndarray,
    values: list[float] | np.ndarray,
    *,
    weather: dict[str, Any] | None = None,
    fetch_weather: bool = False,
) -> dict[str, Any]:
    """Fit ≥16-param SciPy model; apply Fairfax county weather as soft prior bias.

    Returns params, covariance diagonal summary, residuals, and stamp metadata.
    """
    x = np.asarray(circle_frac, dtype=float).ravel()
    y = np.asarray(values, dtype=float).ravel()
    if x.size != y.size:
        raise ValueError("circle_frac and values length mismatch")
    if x.size < N_PARAMS:
        raise ValueError(f"need ≥{N_PARAMS} samples for curve_fit, got {x.size}")

    prior = weather if weather is not None else fairfax_weather_prior(fetch=fetch_weather)
    bias = weather_bias(prior)
    y_adj = y - bias

    popt, pcov = curve_fit(
        model_circle,
        x,
        y_adj,
        p0=_default_p0(),
        maxfev=20000,
    )
    y_hat = model_circle(x, *popt) + bias
    resid = y - y_hat
    rmse = float(np.sqrt(np.mean(resid**2))) if resid.size else 0.0
    cov = np.asarray(pcov, dtype=float)
    return {
        "ok": True,
        "engine": "scipy.optimize.curve_fit",
        "nParams": int(N_PARAMS),
        "nHarmonics": int(N_HARMONICS),
        "n": int(x.size),
        "params": [float(v) for v in popt],
        "paramStderr": [
            float(np.sqrt(max(cov[i, i], 0.0))) if cov.ndim == 2 else float("nan")
            for i in range(N_PARAMS)
        ],
        "rmse": rmse,
        "weatherBias": float(bias),
        "weather": {
            "region": prior.get("region"),
            "grain": prior.get("grain"),
            "mode": prior.get("mode"),
            "tempC": prior.get("tempC"),
            "humidityPct": prior.get("humidityPct"),
            "streetAddress": None,
        },
        "functions": ["scipy.optimize.curve_fit"],
    }
