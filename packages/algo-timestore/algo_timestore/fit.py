"""≥16-parameter nonlinear diurnal circle fit via SciPy curve_fit."""

from __future__ import annotations

from typing import Any

import numpy as np

from .stamp import stamp
from .weather import fairfax_weather_prior, weather_bias

try:
    from scipy.optimize import curve_fit
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "scipy is required for algo_timestore.fit; pin scipy in packages/algo-timestore/requirements.txt"
    ) from exc

# Mean + 7 harmonic pairs (cos/sin) + bounded weather response = 16 parameters.
N_HARMONICS = 7
N_PARAMS = 1 + 2 * N_HARMONICS + 1  # 16
assert N_PARAMS >= 16


def model_circle(model_input: np.ndarray, *params: float) -> np.ndarray:
    """Periodic diurnal Fourier series with an optional weather-response feature.

    ``model_input`` may be a circle-fraction vector or a 2×N array containing
    circle fraction and a periodic weather-response feature.
    """
    p = np.asarray(params, dtype=float).ravel()
    if p.size != N_PARAMS:
        raise ValueError(f"expected {N_PARAMS} params, got {p.size}")
    raw = np.asarray(model_input, dtype=float)
    if raw.ndim == 2:
        if raw.shape[0] != 2:
            raise ValueError("2-D model_input must contain circle and weather rows")
        x = raw[0].ravel()
        weather_feature = raw[1].ravel()
    else:
        x = raw.ravel()
        weather_feature = np.zeros_like(x)
    y = np.full_like(x, p[0], dtype=float)
    for k in range(1, N_HARMONICS + 1):
        a = p[2 * k - 1]
        b = p[2 * k]
        ang = 2.0 * np.pi * k * x
        y = y + a * np.cos(ang) + b * np.sin(ang)
    return y + p[-1] * weather_feature


def _default_p0() -> np.ndarray:
    p0 = np.zeros(N_PARAMS, dtype=float)
    p0[0] = 1.0
    p0[1] = 0.15
    p0[2] = 0.05
    p0[-1] = 1.0
    return p0


def fit_circle_series(
    circle_frac: list[float] | np.ndarray,
    values: list[float] | np.ndarray,
    *,
    weather: dict[str, Any] | None = None,
    fetch_weather: bool | None = None,
) -> dict[str, Any]:
    """Fit the 16-param model with a bounded Fairfax weather-response prior.

    Returns parameters, uncertainty, residuals, RMSE, weather metadata, and stamp.
    """
    x = np.asarray(circle_frac, dtype=float).ravel()
    y = np.asarray(values, dtype=float).ravel()
    if x.size != y.size:
        raise ValueError("circle_frac and values length mismatch")
    if x.size <= N_PARAMS:
        raise ValueError(f"need >{N_PARAMS} samples for uncertainty estimates, got {x.size}")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("circle_frac and values must be finite")
    if np.any((x < 0.0) | (x >= 1.0)):
        raise ValueError("circle_frac values must be in [0, 1)")

    prior = weather if weather is not None else fairfax_weather_prior(fetch=fetch_weather)
    bias = weather_bias(prior)
    weather_feature = bias * np.maximum(np.sin(2.0 * np.pi * (x - 0.25)), 0.0)
    model_input = np.vstack((x, weather_feature))
    lower = np.full(N_PARAMS, -np.inf)
    upper = np.full(N_PARAMS, np.inf)
    lower[-1], upper[-1] = 0.5, 1.5

    popt, pcov = curve_fit(
        model_circle,
        model_input,
        y,
        p0=_default_p0(),
        bounds=(lower, upper),
        maxfev=20000,
    )
    y_hat = model_circle(model_input, *popt)
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
        "residuals": [float(v) for v in resid],
        "weatherBias": float(bias),
        "weatherEffectPeak": float(np.max(np.abs(popt[-1] * weather_feature))),
        "weather": {
            "region": prior.get("region"),
            "grain": prior.get("grain"),
            "mode": prior.get("mode"),
            "tempC": prior.get("tempC"),
            "humidityPct": prior.get("humidityPct"),
            "streetAddress": None,
        },
        "stamp": stamp(meta={"fitSamples": int(x.size)}, include_weather=False),
        "functions": ["scipy.optimize.curve_fit"],
    }
