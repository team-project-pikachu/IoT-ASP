#!/usr/bin/env python3
"""Offline MVP sim for packages/algo-timestore (issue #20)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algo_timestore import (  # noqa: E402
    FAIRFAX_CIRCLE_SIM_ID,
    N_PARAMS,
    TIME_QUANTUM_S,
    experiment_tag,
    fairfax_weather_prior,
    fit_circle_series,
    model_circle,
    stamp,
)


def synthetic_series(n: int = 96) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic diurnal carrier energy with known Fourier content."""
    rng = np.random.default_rng(20)
    x = np.linspace(0.0, 1.0, n, endpoint=False)
    truth = np.zeros(N_PARAMS, dtype=float)
    truth[0] = 1.2
    truth[1] = 0.35
    truth[2] = -0.12
    truth[3] = 0.08
    truth[4] = 0.04
    truth[-1] = 0.02
    y = model_circle(x, *truth) + rng.normal(0.0, 0.03, size=n)
    return x, y


def main() -> int:
    x, y = synthetic_series()
    result = fit_circle_series(x, y, fetch_weather=None)
    tag = experiment_tag(FAIRFAX_CIRCLE_SIM_ID)
    weather = fairfax_weather_prior(fetch=None)
    out = {
        "ok": bool(result.get("ok")),
        "quantumS": TIME_QUANTUM_S,
        "nParams": result["nParams"],
        "rmse": result["rmse"],
        "cipher": tag,
        "stamp": stamp(experiment=FAIRFAX_CIRCLE_SIM_ID),
        "weatherMode": weather.get("mode"),
        "fit": {
            "engine": result["engine"],
            "n": result["n"],
            "weatherBias": result["weatherBias"],
            "weatherEffectPeak": result["weatherEffectPeak"],
            "paramsHead": result["params"][:4],
        },
    }
    print(json.dumps(out, indent=2))
    assert result["nParams"] >= 16
    assert result["rmse"] < 0.2
    assert result["weatherEffectPeak"] > 0.0
    assert len(result["residuals"]) == len(x)
    assert weather.get("streetAddress") is None
    try:
        fit_circle_series(x[:N_PARAMS], y[:N_PARAMS], weather=weather)
    except ValueError as exc:
        assert f">{N_PARAMS}" in str(exc)
    else:
        raise AssertionError("fit must reject zero residual degrees of freedom")
    print(
        f"\n# timestore sim ok: nParams={result['nParams']} rmse={result['rmse']:.4f} "
        f"quantum={TIME_QUANTUM_S}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
