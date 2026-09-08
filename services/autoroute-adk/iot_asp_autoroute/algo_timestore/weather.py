"""Fairfax County weather prior — county centroid only, no street addresses."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

# Fairfax County, VA approximate geographic centroid (public county-scale prior).
# Do NOT store or request street addresses / site PII.
FAIRFAX_COUNTY_CENTROID = {
    "lat": 38.8462,
    "lon": -77.3064,
    "region": "Fairfax County, VA",
    "grain": "county",
    "source": "open-meteo|climate-fallback",
}

# Rough climate fallback when network fetch is disabled (no live API required for CI).
_CLIMATE_FALLBACK = {
    "tempC": 18.0,
    "humidityPct": 55.0,
    "windMs": 3.0,
    "precipMm": 0.0,
    "mode": "climate-fallback",
}


def _open_meteo_url(lat: float, lon: float) -> str:
    return (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat:.4f}&longitude={lon:.4f}"
        "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
        "&timezone=America%2FNew_York"
    )


def fairfax_weather_prior(*, fetch: bool | None = None, timeout_s: float = 4.0) -> dict[str, Any]:
    """County-scale weather features for timestore soft priors.

    Live fetch only when ``fetch=True`` or env ``IOT_ASP_TIMESTORE_FETCH_WEATHER=1``.
    Default is offline climate fallback so local sim / CI stay deterministic.
    """
    if fetch is None:
        fetch = os.environ.get("IOT_ASP_TIMESTORE_FETCH_WEATHER", "").strip() in (
            "1",
            "true",
            "TRUE",
            "yes",
        )

    base: dict[str, Any] = {
        "region": FAIRFAX_COUNTY_CENTROID["region"],
        "grain": "county",
        "lat": FAIRFAX_COUNTY_CENTROID["lat"],
        "lon": FAIRFAX_COUNTY_CENTROID["lon"],
        "streetAddress": None,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "open-meteo",
    }

    if not fetch:
        out = {**base, **_CLIMATE_FALLBACK}
        out["ok"] = True
        return out

    url = _open_meteo_url(base["lat"], base["lon"])
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "iot-asp-timestore/0.1"})
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        cur = payload.get("current") or {}
        out = {
            **base,
            "ok": True,
            "mode": "live",
            "tempC": float(cur.get("temperature_2m", _CLIMATE_FALLBACK["tempC"])),
            "humidityPct": float(
                cur.get("relative_humidity_2m", _CLIMATE_FALLBACK["humidityPct"])
            ),
            "windMs": float(cur.get("wind_speed_10m", _CLIMATE_FALLBACK["windMs"])),
            "precipMm": float(cur.get("precipitation", _CLIMATE_FALLBACK["precipMm"])),
        }
        return out
    except (
        urllib.error.URLError,
        TimeoutError,
        TypeError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ):
        out = {**base, **_CLIMATE_FALLBACK, "ok": True, "mode": "climate-fallback-after-error"}
        return out


def weather_bias(prior: dict[str, Any]) -> float:
    """Soft additive bias for circle model from county weather (unitless)."""
    temp = float(prior.get("tempC", 18.0))
    hum = float(prior.get("humidityPct", 55.0))
    wind = float(prior.get("windMs", 3.0))
    # Normalize around mild Fairfax day; keep small so fit stays stable.
    return 0.02 * (temp - 18.0) / 10.0 + 0.01 * (hum - 55.0) / 20.0 + 0.005 * wind
