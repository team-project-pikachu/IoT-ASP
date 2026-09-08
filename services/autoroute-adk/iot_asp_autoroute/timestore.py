"""Adapter from autoroute to the standalone algo-timestore package."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TIMESTORE_ROOT = _REPO_ROOT / "packages" / "algo-timestore"
if str(_TIMESTORE_ROOT) not in sys.path:
    sys.path.insert(0, str(_TIMESTORE_ROOT))

from algo_timestore import N_PARAMS, TIME_QUANTUM_S, stamp  # noqa: E402


def autoroute_timestore_prior() -> dict[str, Any]:
    """Return time-aware routing context backed by the shared timestore."""
    current = stamp(include_weather=False)
    return {
        "circleUtc": current["circleUtc"],
        "horizonYears": current["horizonYears"],
        "quantumS": TIME_QUANTUM_S,
        "fitParams": N_PARAMS,
        "engine": current["engine"],
    }


def autoroute_telemetry_stamp() -> dict[str, Any]:
    """Return a protected timestore sidecar for telemetry persistence."""
    return stamp(include_weather=False)
