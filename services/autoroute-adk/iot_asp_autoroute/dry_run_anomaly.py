"""Offline dry-run: SciPy vib anomaly on synthetic 1 Hz series (no Vertex/ADK)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PKG = Path(__file__).resolve().parent
_ROOT = _PKG.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from iot_asp_autoroute.vib_anomaly import (  # noqa: E402
    VIB_QUANTUM,
    detect_disturbances,
    synthetic_demo_series,
)


def main() -> int:
    series = synthetic_demo_series(60)
    result = detect_disturbances(series, quantum=VIB_QUANTUM, sample_hz=1.0)
    print(json.dumps(result, indent=2))
    flags = sum(1 for a in result["anomaly"] if a)
    print(
        f"\n# SciPy anomaly dry-run: n={result['n']} anomalies={flags} "
        f"disturbance={result['disturbance']} quantum={VIB_QUANTUM} g "
        f"funcs={result['functions']}",
        file=sys.stderr,
    )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
