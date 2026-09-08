"""Adapter from autoroute to the standalone algo-timestore package."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TIMESTORE_ROOT = _REPO_ROOT / "packages" / "algo-timestore"
if str(_TIMESTORE_ROOT) not in sys.path:
    sys.path.insert(0, str(_TIMESTORE_ROOT))


def _load_timestore() -> Any:
    """Load the SciPy-backed package only when a timestore operation is requested."""
    return importlib.import_module("algo_timestore")


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
