"""Compact timestore stamps for telemetry sidecars (no site PII)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .ciphers import experiment_tag
from .quantum import TIME_QUANTUM_S, circle_fraction_utc, quantize_posix
from .weather import fairfax_weather_prior


def stamp(
    meta: dict[str, Any] | None = None,
    *,
    experiment: str | None = None,
    include_weather: bool = True,
) -> dict[str, Any]:
    """Build a timestore stamp; optional cipher tag + county weather prior."""
    now = datetime.now(timezone.utc).timestamp()
    q = quantize_posix(now)
    out: dict[str, Any] = {
        "ts": datetime.fromtimestamp(q, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "posixQ": q,
        "quantumS": TIME_QUANTUM_S,
        "circleUtc": round(circle_fraction_utc(q), 6),
        "horizonYears": 1.0,
        "engine": "algo-timestore",
        "nParams": 16,
    }
    if experiment:
        out["cipher"] = experiment_tag(experiment)
    if include_weather:
        w = fairfax_weather_prior(fetch=False)
        out["weather"] = {
            "region": w["region"],
            "grain": w["grain"],
            "mode": w["mode"],
            "tempC": w["tempC"],
            "streetAddress": None,
        }
    if meta:
        out.update(meta)
    return out
