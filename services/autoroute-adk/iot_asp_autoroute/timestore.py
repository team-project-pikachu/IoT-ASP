"""Adapter from autoroute to the vendored algo_timestore subpackage.

Canonical source lives at ``packages/algo-timestore/``; ADK deploy only ships
``iot_asp_autoroute/``, so the library is copied under
``iot_asp_autoroute/algo_timestore/`` (see ``scripts/sync_algo_timestore_to_adk.sh``).
"""

from __future__ import annotations

from typing import Any

from . import algo_timestore


def autoroute_timestore_prior() -> dict[str, Any]:
    """Return time-aware routing context backed by the shared timestore."""
    current = algo_timestore.stamp(include_weather=False)
    return {
        "circleUtc": current["circleUtc"],
        "horizonYears": current["horizonYears"],
        "quantumS": algo_timestore.TIME_QUANTUM_S,
        "fitParams": algo_timestore.N_PARAMS,
        "engine": current["engine"],
    }


def autoroute_telemetry_stamp() -> dict[str, Any]:
    """Return a protected timestore sidecar for telemetry persistence."""
    return algo_timestore.stamp(include_weather=False)
