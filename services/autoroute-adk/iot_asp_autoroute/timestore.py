"""Adapter from autoroute to the vendored algo_timestore subpackage.

Canonical source lives at ``packages/algo-timestore/``; ADK deploy only ships
``iot_asp_autoroute/``, so the library is copied under
``iot_asp_autoroute/algo_timestore/`` (see ``scripts/sync_algo_timestore_to_adk.sh``).

Import is **lazy**: ``priors`` / ``fleet_log`` / ``mic_diff`` must not pull numpy/scipy
at module import time (see ``tests/test_fleet_log.py`` hygiene + ``test_md15_*``).
Relative import keeps ADK packaging safe (no monorepo path insertion / parents[N] hacks).
"""

from __future__ import annotations

from typing import Any


def _load_timestore() -> Any:
    """Load the SciPy-backed vendored subpackage only when a stamp/prior is requested."""
    from . import algo_timestore

    return algo_timestore


def autoroute_timestore_prior() -> dict[str, Any]:
    """Return time-aware routing context backed by the shared timestore."""
    timestore = _load_timestore()
    current = timestore.stamp(include_weather=False)
    return {
        "circleUtc": current["circleUtc"],
        "horizonYears": current["horizonYears"],
        "quantumS": timestore.TIME_QUANTUM_S,
        "fitParams": timestore.N_PARAMS,
        "engine": current["engine"],
    }


def autoroute_telemetry_stamp() -> dict[str, Any]:
    """Return a protected timestore sidecar for telemetry persistence."""
    return _load_timestore().stamp(include_weather=False)
